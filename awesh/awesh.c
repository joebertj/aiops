#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include <readline/readline.h>
#include <readline/history.h>

#define SOCKET_PATH "/tmp/awesh.sock"
#define MAX_CMD_LEN 4096
#define MAX_RESPONSE_LEN 65536

typedef enum {
    AI_LOADING,
    AI_READY,
    AI_FAILED
} ai_status_t;

typedef struct {
    int backend_pid;
    int socket_fd;
    ai_status_t ai_status;
    int show_ai_status;  // 1 = show, 0 = hide
} awesh_state_t;

static awesh_state_t state = {0, -1, AI_LOADING, 1};

void load_config() {
    // Read ~/.aweshrc for configuration
    char config_path[512];
    snprintf(config_path, sizeof(config_path), "%s/.aweshrc", getenv("HOME"));
    
    FILE *file = fopen(config_path, "r");
    if (!file) return;  // No config file, use defaults
    
    char line[256];
    while (fgets(line, sizeof(line), file)) {
        // Remove newline
        line[strcspn(line, "\n")] = 0;
        
        // Skip empty lines and comments
        if (line[0] == '\0' || line[0] == '#') continue;
        
        // Parse key=value pairs
        char *equals = strchr(line, '=');
        if (!equals) continue;
        
        *equals = '\0';
        char *key = line;
        char *value = equals + 1;
        
        if (strcmp(key, "SHOW_AI_STATUS") == 0) {
            state.show_ai_status = (strcmp(value, "false") != 0 && strcmp(value, "0") != 0);
        }
    }
    
    fclose(file);
}

void cleanup_and_exit(int sig) {
    if (state.socket_fd >= 0) {
        close(state.socket_fd);
    }
    if (state.backend_pid > 0) {
        kill(state.backend_pid, SIGTERM);
        waitpid(state.backend_pid, NULL, 0);
    }
    unlink(SOCKET_PATH);
    printf("\nGoodbye!\n");
    exit(0);
}

int start_backend() {
    // Remove existing socket
    unlink(SOCKET_PATH);
    
    // Fork backend process
    state.backend_pid = fork();
    if (state.backend_pid == 0) {
        // Child: start Python backend
        execl("/usr/bin/python3", "python3", "backend_socket.py", NULL);
        perror("Failed to start backend");
        exit(1);
    } else if (state.backend_pid < 0) {
        perror("Failed to fork backend");
        return -1;
    }
    
    // Parent: wait a bit for backend to start
    sleep(1);
    
    // Connect to backend socket
    state.socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (state.socket_fd < 0) {
        perror("Failed to create socket");
        return -1;
    }
    
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);
    
    if (connect(state.socket_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("Failed to connect to backend");
        close(state.socket_fd);
        state.socket_fd = -1;
        return -1;
    }
    
    return 0;
}

void check_ai_status() {
    if (state.socket_fd < 0) return;
    
    // Send status check
    if (send(state.socket_fd, "STATUS", 6, 0) < 0) return;
    
    // Read response
    char response[64];
    ssize_t bytes = recv(state.socket_fd, response, sizeof(response) - 1, 0);
    if (bytes > 0) {
        response[bytes] = '\0';
        if (strncmp(response, "AI_READY", 8) == 0) {
            state.ai_status = AI_READY;
        } else if (strncmp(response, "AI_LOADING", 10) == 0) {
            state.ai_status = AI_LOADING;
        }
    }
}

void send_command(const char* cmd) {
    if (state.socket_fd < 0) {
        // No backend - execute directly with system()
        system(cmd);
        return;
    }
    
    // Send command to backend
    char buffer[MAX_CMD_LEN];
    snprintf(buffer, sizeof(buffer), "%s", cmd);
    
    if (send(state.socket_fd, buffer, strlen(buffer), 0) < 0) {
        perror("Failed to send command");
        return;
    }
    
    // Read response
    char response[MAX_RESPONSE_LEN];
    ssize_t bytes = recv(state.socket_fd, response, sizeof(response) - 1, 0);
    if (bytes > 0) {
        response[bytes] = '\0';
        
        // Check if backend wants us to handle interactive command
        if (strncmp(response, "INTERACTIVE:", 12) == 0) {
            const char* interactive_cmd = response + 12;
            // Remove trailing newline
            char* newline = strchr(interactive_cmd, '\n');
            if (newline) *newline = '\0';
            
            system(interactive_cmd);
        } else {
            printf("%s", response);
        }
        
        // Check AI status after command (efficient - we're already communicating)
        if (state.ai_status == AI_LOADING) {
            check_ai_status();
        }
    }
}

int is_builtin(const char* cmd) {
    return (strncmp(cmd, "cd ", 3) == 0 || 
            strcmp(cmd, "pwd") == 0 || 
            strcmp(cmd, "exit") == 0);
}

void handle_builtin(const char* cmd) {
    if (strcmp(cmd, "exit") == 0) {
        cleanup_and_exit(0);
    } else if (strcmp(cmd, "pwd") == 0) {
        char cwd[1024];
        if (getcwd(cwd, sizeof(cwd))) {
            printf("%s\n", cwd);
        }
    } else if (strncmp(cmd, "cd ", 3) == 0) {
        const char* path = cmd + 3;
        if (chdir(path) != 0) {
            perror("cd");
        }
    }
}

int main() {
    // Setup signal handlers
    signal(SIGINT, cleanup_and_exit);
    signal(SIGTERM, cleanup_and_exit);
    
    // Load configuration
    load_config();
    
    // Start backend silently
    printf("awesh v0.1.0 - Awe-Inspired Workspace Environment Shell\n\n");
    
    if (start_backend() != 0) {
        state.ai_status = AI_FAILED;
    }
    
    // Main shell loop
    char* line;
    char prompt[64];
    
    while (1) {
        // Dynamic prompt with optional AI status
        if (state.show_ai_status) {
            switch (state.ai_status) {
                case AI_LOADING:
                    snprintf(prompt, sizeof(prompt), "AI loading: awesh> ");
                    break;
                case AI_READY:
                    snprintf(prompt, sizeof(prompt), "AI ready: awesh> ");
                    break;
                case AI_FAILED:
                    snprintf(prompt, sizeof(prompt), "awesh> ");
                    break;
            }
        } else {
            snprintf(prompt, sizeof(prompt), "awesh> ");
        }
        
        // Get input with readline (supports history, editing)
        line = readline(prompt);
        
        if (!line) {
            // EOF (Ctrl+D)
            break;
        }
        
        if (strlen(line) == 0) {
            free(line);
            continue;
        }
        
        // Add to history
        add_history(line);
        
        // Handle command
        if (is_builtin(line)) {
            handle_builtin(line);
        } else {
            send_command(line);
        }
        
        free(line);
    }
    
    cleanup_and_exit(0);
    return 0;
}
