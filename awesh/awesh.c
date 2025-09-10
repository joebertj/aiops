#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/select.h>
#include <signal.h>
#include <errno.h>
#include <readline/readline.h>
#include <readline/history.h>

static char socket_path[512];

void init_socket_path() {
    const char* home = getenv("HOME");
    if (home) {
        snprintf(socket_path, sizeof(socket_path), "%s/.awesh.sock", home);
    } else {
        strcpy(socket_path, "/tmp/awesh.sock");  // fallback
    }
}
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
    int verbose;         // 0 = silent, 1 = show AI status + debug, 2+ = more verbose
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
        
        if (strcmp(key, "VERBOSE") == 0) {
            state.verbose = atoi(value);  // Parse as integer: 0=silent, 1=show AI status+debug, 2+=more verbose
        }
        
        // Set all config values as environment variables for backend
        setenv(key, value, 1);
    }
    
    fclose(file);
}

void update_config_file(const char* key, const char* value) {
    char config_path[512];
    snprintf(config_path, sizeof(config_path), "%s/.aweshrc", getenv("HOME"));
    
    // Read existing config
    char lines[100][256];  // Max 100 lines, 256 chars each
    int line_count = 0;
    int key_found = 0;
    
    FILE *file = fopen(config_path, "r");
    if (file) {
        while (fgets(lines[line_count], sizeof(lines[line_count]), file) && line_count < 99) {
            // Remove newline for processing
            lines[line_count][strcspn(lines[line_count], "\n")] = 0;
            
            // Check if this line contains our key
            if (strncmp(lines[line_count], key, strlen(key)) == 0 && 
                lines[line_count][strlen(key)] == '=') {
                // Update existing key
                snprintf(lines[line_count], sizeof(lines[line_count]), "%s=%s", key, value);
                key_found = 1;
            }
            line_count++;
        }
        fclose(file);
    }
    
    // If key wasn't found, add it
    if (!key_found && line_count < 99) {
        snprintf(lines[line_count], sizeof(lines[line_count]), "%s=%s", key, value);
        line_count++;
    }
    
    // Write back to file
    file = fopen(config_path, "w");
    if (file) {
        for (int i = 0; i < line_count; i++) {
            fprintf(file, "%s\n", lines[i]);
        }
        fclose(file);
    }
}

void handle_sigint(int sig __attribute__((unused))) {
    // Ctrl+C should just return to prompt, not exit
    printf("\n");
    rl_on_new_line();
    rl_replace_line("", 0);
    rl_redisplay();
}

void cleanup_and_exit(int sig __attribute__((unused))) {
    if (state.socket_fd >= 0) {
        close(state.socket_fd);
    }
    if (state.backend_pid > 0) {
        kill(state.backend_pid, SIGTERM);
        waitpid(state.backend_pid, NULL, 0);
    }
    unlink(socket_path);
    printf("\nGoodbye!\n");
    exit(0);
}

int start_backend() {
    // Initialize socket path
    init_socket_path();
    
    // Remove existing socket
    unlink(socket_path);
    
    // Fork backend process
    state.backend_pid = fork();
    if (state.backend_pid == 0) {
        // Child: start Python backend as module using virtual environment
        const char* home = getenv("HOME");
        char venv_python[512];
        
        // Try to use virtual environment Python first
        if (home) {
            snprintf(venv_python, sizeof(venv_python), "%s/AI/aiops/venv/bin/python3", home);
            if (access(venv_python, X_OK) == 0) {
                execl(venv_python, "python3", "-m", "awesh_backend", NULL);
            }
        }
        
        // Fallback to system Python
        execl("/usr/bin/python3", "python3", "-m", "awesh_backend", NULL);
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
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);
    
    if (connect(state.socket_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("Failed to connect to backend");
        close(state.socket_fd);
        state.socket_fd = -1;
        return -1;
    }
    
    return 0;
}

void check_ai_status() {
    if (state.socket_fd < 0) {
        if (state.verbose >= 1) {
            printf("🔧 Status check: No socket connection\n");
        }
        return;
    }
    
    if (state.verbose >= 1) {
        printf("🔧 Sending STATUS command...\n");
    }
    
    // Send status check
    if (send(state.socket_fd, "STATUS", 6, 0) < 0) {
        if (state.verbose >= 1) {
            printf("🔧 Failed to send STATUS command\n");
        }
        return;
    }
    
    // Read response
    char response[64];
    ssize_t bytes = recv(state.socket_fd, response, sizeof(response) - 1, 0);
    if (bytes > 0) {
        response[bytes] = '\0';
        if (state.verbose >= 1) {
            printf("🔧 Status response: '%s' (%zd bytes)\n", response, bytes);
        }
        if (strncmp(response, "AI_READY", 8) == 0) {
            state.ai_status = AI_READY;
            if (state.verbose >= 1) {
                printf("🔧 AI status updated to READY\n");
            }
        } else if (strncmp(response, "AI_LOADING", 10) == 0) {
            state.ai_status = AI_LOADING;
            if (state.verbose >= 1) {
                printf("🔧 AI status updated to LOADING\n");
            }
        } else {
            if (state.verbose >= 1) {
                printf("🔧 Unknown status response: '%s'\n", response);
            }
        }
    } else {
        if (state.verbose >= 1) {
            printf("🔧 No response to STATUS command (bytes=%zd)\n", bytes);
        }
    }
}

void send_command(const char* cmd) {
    if (state.socket_fd < 0) {
        // No backend - execute directly with system()
        system(cmd);
        return;
    }
    
    // First, sync working directory with backend
    char cwd[1024];
    if (getcwd(cwd, sizeof(cwd))) {
        char sync_buffer[1100];
        snprintf(sync_buffer, sizeof(sync_buffer), "CWD:%s", cwd);
        send(state.socket_fd, sync_buffer, strlen(sync_buffer), 0);
        
        // Wait for sync acknowledgment (brief)
        fd_set readfds;
        struct timeval timeout;
        FD_ZERO(&readfds);
        FD_SET(state.socket_fd, &readfds);
        timeout.tv_sec = 1;
        timeout.tv_usec = 0;
        
        if (select(state.socket_fd + 1, &readfds, NULL, NULL, &timeout) > 0) {
            char ack[64];
            recv(state.socket_fd, ack, sizeof(ack) - 1, 0);  // Consume sync response
        }
    }
    
    // Send actual command to backend
    char buffer[MAX_CMD_LEN];
    snprintf(buffer, sizeof(buffer), "%s", cmd);
    
    if (send(state.socket_fd, buffer, strlen(buffer), 0) < 0) {
        perror("Failed to send command");
        return;
    }
    
    // Read response with timeout and thinking dots
    fd_set readfds;
    struct timeval timeout;
    int dots_shown = 0;
    
    while (1) {
        FD_ZERO(&readfds);
        FD_SET(state.socket_fd, &readfds);
        timeout.tv_sec = 5;  // 5 second intervals for dots
        timeout.tv_usec = 0;
        
        int select_result = select(state.socket_fd + 1, &readfds, NULL, NULL, &timeout);
        
        if (select_result > 0) {
            // Data available - break out to read response
            break;
        } else if (select_result == 0) {
            // Timeout - show thinking dot
            printf(".");
            fflush(stdout);
            dots_shown++;
            
            // Stop after 64 dots (5+ minutes)
            if (dots_shown >= 64) {
                printf("\nBackend timeout - no response\n");
                return;
            }
        } else {
            perror("select failed");
            return;
        }
    }
    
    // Clear dots line if any were shown
    if (dots_shown > 0) {
        printf("\n");
    }
    
    int select_result = 1; // We know data is available
    if (select_result > 0) {
        char response[MAX_RESPONSE_LEN];
        ssize_t bytes = recv(state.socket_fd, response, sizeof(response) - 1, 0);
        if (bytes > 0) {
            response[bytes] = '\0';
            
            printf("%s", response);
            
            // Check AI status after command (efficient - we're already communicating)
            if (state.ai_status == AI_LOADING) {
                check_ai_status();
            }
        } else if (bytes == 0) {
            printf("Backend disconnected\n");
        } else {
            perror("recv failed");
        }
    } else if (select_result == 0) {
        printf("Backend timeout - no response\n");
    } else {
        perror("select failed");
    }
}

int is_awesh_command(const char* cmd) {
    return (strcmp(cmd, "aweh") == 0 ||
            strcmp(cmd, "awes") == 0 ||
            strncmp(cmd, "awev", 4) == 0 ||
            strncmp(cmd, "awea", 4) == 0);
}

int is_builtin(const char* cmd) {
    return (strncmp(cmd, "cd ", 3) == 0 || 
            strcmp(cmd, "cd") == 0 ||
            strcmp(cmd, "pwd") == 0 || 
            strcmp(cmd, "exit") == 0);
}

void handle_awesh_command(const char* cmd) {
    if (strcmp(cmd, "aweh") == 0) {
        printf("🎛️  Awesh Control Commands:\n");
        printf("\n📋 Help:\n");
        printf("  aweh              Show this help\n");
        printf("  awes              Show verbose status (API provider, model, debug state)\n");
        printf("\n🔧 Verbose Debug:\n");
        printf("  awev              Show verbose level status\n");
        printf("  awev 0            Set verbose level 0 (silent)\n");
        printf("  awev 1            Set verbose level 1 (info)\n");
        printf("  awev 2            Set verbose level 2 (debug)\n");
        printf("  awev on           Enable verbose logging (level 1)\n");
        printf("  awev off          Disable verbose logging (level 0)\n");
        printf("\n🤖 AI Provider:\n");
        printf("  awea              Show current AI provider and model\n");
        printf("  awea openai       Switch to OpenAI\n");
        printf("  awea openrouter   Switch to OpenRouter\n");
        printf("\n💡 All commands use 'awe' prefix to avoid bash conflicts\n");
    } else if (strcmp(cmd, "awes") == 0) {
        const char* ai_provider = getenv("AI_PROVIDER") ? getenv("AI_PROVIDER") : "openai";
        const char* model = getenv("MODEL") ? getenv("MODEL") : "not configured";
        
        // Verbose status - show everything
        printf("🔍 Awesh Verbose Status:\n");
        printf("🤖 API Provider: %s\n", ai_provider);
        printf("📋 Model: %s\n", model);
        printf("🔧 Debug Logging: %s\n", state.verbose ? "enabled" : "disabled");
        printf("📡 AI Status: ");
        switch (state.ai_status) {
            case AI_LOADING:
                printf("loading\n");
                break;
            case AI_READY:
                printf("ready\n");
                break;
            case AI_FAILED:
                printf("failed\n");
                break;
        }
        printf("📊 Backend PID: %d\n", state.backend_pid);
        printf("🔌 Socket FD: %d\n", state.socket_fd);
        printf("🔧 Verbose Level: %d (0=silent, 1=info, 2=debug)\n", state.verbose);
    } else if (strncmp(cmd, "awev", 4) == 0) {
        // Parse awev command and arguments
        if (strcmp(cmd, "awev") == 0) {
            // Just "awev" - show status
            printf("🔧 Verbose Level: %d (0=silent, 1=info, 2=debug)\n", state.verbose);
        } else if (strcmp(cmd, "awev 0") == 0) {
            // Set verbose level 0 (silent)
            update_config_file("VERBOSE", "0");
            send_command("VERBOSE:0");
            state.verbose = 0;
            printf("🔧 Verbose level set to 0 (silent)\n");
        } else if (strcmp(cmd, "awev 1") == 0) {
            // Set verbose level 1 (info)
            update_config_file("VERBOSE", "1");
            send_command("VERBOSE:1");
            state.verbose = 1;
            printf("🔧 Verbose level set to 1 (info)\n");
        } else if (strcmp(cmd, "awev 2") == 0) {
            // Set verbose level 2 (debug)
            update_config_file("VERBOSE", "2");
            send_command("VERBOSE:2");
            state.verbose = 2;
            printf("🔧 Verbose level set to 2 (debug)\n");
        } else if (strcmp(cmd, "awev on") == 0) {
            // Legacy: Enable verbose logging (level 1)
            update_config_file("VERBOSE", "1");
            send_command("VERBOSE:1");
            state.verbose = 1;
            printf("🔧 Verbose logging enabled (level 1)\n");
        } else if (strcmp(cmd, "awev off") == 0) {
            // Legacy: Disable verbose logging (level 0)
            update_config_file("VERBOSE", "0");
            send_command("VERBOSE:0");
            state.verbose = 0;
            printf("🔧 Verbose logging disabled (level 0)\n");
        } else {
            printf("Usage: awev [0|1|2|on|off]\n");
        }
    } else if (strncmp(cmd, "awea", 4) == 0) {
        const char* ai_provider = getenv("AI_PROVIDER") ? getenv("AI_PROVIDER") : "openai";
        const char* model = NULL;
        
        if (strcmp(ai_provider, "openrouter") == 0) {
            model = getenv("OPENROUTER_MODEL") ? getenv("OPENROUTER_MODEL") : "not configured";
        } else {
            model = getenv("OPENAI_MODEL") ? getenv("OPENAI_MODEL") : "not configured";
        }
        
        // Parse awea command and arguments
        if (strcmp(cmd, "awea") == 0) {
            // Just "awea" - show current provider and model
            printf("🤖 API Provider: %s\n", ai_provider);
            printf("📋 Model: %s\n", model);
        } else if (strcmp(cmd, "awea openai") == 0) {
            // Switch to OpenAI
            update_config_file("AI_PROVIDER", "openai");
            send_command("AI_PROVIDER:openai");
            printf("🤖 Switching to OpenAI... (restart awesh to take effect)\n");
        } else if (strcmp(cmd, "awea openrouter") == 0) {
            // Switch to OpenRouter
            update_config_file("AI_PROVIDER", "openrouter");
            send_command("AI_PROVIDER:openrouter");
            printf("🤖 Switching to OpenRouter... (restart awesh to take effect)\n");
        } else {
            printf("Usage: awea [openai|openrouter]\n");
        }
    }
}

int is_interactive_bash_command(const char* cmd) {
    if (!cmd || strlen(cmd) == 0) return 0;
    
    // Interactive commands that should run directly in C frontend
    const char* interactive_commands[] = {
        "vi", "vim", "nano", "emacs", "htop", "top", "less", "more", 
        "man", "ssh", "ftp", "telnet", "mysql", "psql", "python", 
        "python3", "node", "irb", "bash", "sh", "zsh", "sudo"
    };
    
    char cmd_copy[MAX_CMD_LEN];
    strncpy(cmd_copy, cmd, sizeof(cmd_copy) - 1);
    cmd_copy[sizeof(cmd_copy) - 1] = '\0';
    
    char* first_word = strtok(cmd_copy, " \t");
    if (!first_word) return 0;
    
    // Check if first word is interactive
    for (int i = 0; i < sizeof(interactive_commands) / sizeof(interactive_commands[0]); i++) {
        if (strcmp(first_word, interactive_commands[i]) == 0) {
            return 1;
        }
    }
    
    return 0;
}

void handle_interactive_bash(const char* cmd) {
    int result = system(cmd);
    if (result != 0 && state.verbose >= 1) {
        printf("Command exited with code: %d\n", result);
    }
}

void handle_bash_with_ai_fallback(const char* cmd) {
    // If AI is ready, try bash and capture output for AI context
    if (state.socket_fd >= 0 && state.ai_status == AI_READY) {
        // Capture both stdout and stderr for AI context
        char temp_file[] = "/tmp/awesh_bash_XXXXXX";
        int fd = mkstemp(temp_file);
        if (fd != -1) {
            close(fd);
            
            char bash_cmd[MAX_CMD_LEN + 100];
            snprintf(bash_cmd, sizeof(bash_cmd), "%s >%s 2>&1", cmd, temp_file);
            int result = system(bash_cmd);
            
            if (result == 0) {
                // Bash succeeded - show output and clean up
                char cat_cmd[200];
                snprintf(cat_cmd, sizeof(cat_cmd), "cat %s", temp_file);
                system(cat_cmd);
                unlink(temp_file);
            } else {
                // Bash failed - send command and output to AI as context
                if (state.verbose >= 1) {
                    printf("Command failed (exit %d), trying AI assistance...\n", result);
                    // Debug: show what was captured
                    printf("🔧 Error output captured in temp file:\n");
                    char cat_debug[200];
                    snprintf(cat_debug, sizeof(cat_debug), "cat %s", temp_file);
                    system(cat_debug);
                    printf("🔧 End of captured output\n");
                }
                
                // Send command with bash failure context to backend
                char context_cmd[MAX_CMD_LEN + 200];
                snprintf(context_cmd, sizeof(context_cmd), "BASH_FAILED:%d:%s:%s", result, cmd, temp_file);
                send_command(context_cmd);
                unlink(temp_file);
            }
        } else {
            // Fallback if temp file creation fails
            int result = system(cmd);
            if (result != 0 && state.verbose >= 1) {
                printf("Command failed (exit %d), trying AI assistance...\n", result);
                send_command(cmd);
            }
        }
    } else {
        // No AI available, run bash normally (show errors)
        system(cmd);
    }
}

void handle_builtin(const char* cmd) {
    if (strcmp(cmd, "exit") == 0) {
        cleanup_and_exit(0);
    } else if (strcmp(cmd, "pwd") == 0) {
        char cwd[1024];
        if (getcwd(cwd, sizeof(cwd))) {
            printf("%s\n", cwd);
        }
    } else if (strncmp(cmd, "cd ", 3) == 0 || strcmp(cmd, "cd") == 0) {
        // Handle cd command in frontend and sync with backend
        const char* path;
        if (strcmp(cmd, "cd") == 0) {
            path = getenv("HOME");  // cd with no args goes to home
        } else {
            path = cmd + 3;  // cd with path
        }
        
        if (chdir(path) == 0) {
            // Success - directory changed instantly
            // Backend will sync on next command that needs it
        } else {
            perror("cd");
        }
    }
}

int main() {
    // Setup signal handlers
    signal(SIGINT, handle_sigint);     // Ctrl+C returns to prompt
    signal(SIGTERM, cleanup_and_exit); // SIGTERM exits cleanly
    
    // Load configuration
    load_config();
    
    // Set VERBOSE environment variable for backend
    char verbose_str[8];
    snprintf(verbose_str, sizeof(verbose_str), "%d", state.verbose);
    setenv("VERBOSE", verbose_str, 1);
    
    // Start backend silently
    printf("awesh v0.1.0 - Awe-Inspired Workspace Environment Shell\n");
    printf("💡 Type 'aweh' to see available control commands\n\n");
    
    if (start_backend() != 0) {
        state.ai_status = AI_FAILED;
    }
    
    // Give backend time to initialize, then check AI status
    sleep(1);
    if (state.socket_fd >= 0) {
        check_ai_status();
    }
    
    // Main shell loop
    char* line;
    char prompt[512];  // Increased size for full path
    
    while (1) {
        // Get username and hostname for prompt
        char* username = getenv("USER");
        if (!username) username = "user";
        
        char hostname[64];
        if (gethostname(hostname, sizeof(hostname)) != 0) {
            strcpy(hostname, "localhost");
        }
        
        // Get current working directory
        char cwd[256];
        if (getcwd(cwd, sizeof(cwd)) == NULL) {
            strcpy(cwd, "~");
        } else {
            // Replace home directory with ~
            char* home = getenv("HOME");
            if (home && strncmp(cwd, home, strlen(home)) == 0) {
                char temp[256];
                snprintf(temp, sizeof(temp), "~%s", cwd + strlen(home));
                strcpy(cwd, temp);
            }
        }
        
        // Color-code username: red for root, green for normal user
        char* user_color = (getuid() == 0) ? "\033[31m" : "\033[32m";  // Red for root, green for user
        
        // Dynamic prompt with color-coded AI status (always shown)
        switch (state.ai_status) {
            case AI_LOADING:
                snprintf(prompt, sizeof(prompt), "\033[31mAI\033[0m:%s%s\033[0m@\033[36m%s\033[0m:\033[34m%s\033[0m\n> ", user_color, username, hostname, cwd);
                break;
            case AI_READY:
                snprintf(prompt, sizeof(prompt), "\033[32mAI\033[0m:%s%s\033[0m@\033[36m%s\033[0m:\033[34m%s\033[0m\n> ", user_color, username, hostname, cwd);
                break;
            case AI_FAILED:
                snprintf(prompt, sizeof(prompt), "\033[31mAI\033[0m:%s%s\033[0m@\033[36m%s\033[0m:\033[34m%s\033[0m\n> ", user_color, username, hostname, cwd);
                break;
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
        
        // Handle command - priority order
        if (is_awesh_command(line)) {
            handle_awesh_command(line);
        } else if (is_builtin(line)) {
            handle_builtin(line);
        } else if (is_interactive_bash_command(line)) {
            handle_interactive_bash(line);
        } else {
            // Try bash directly first, send to backend only on failure or for AI help
            handle_bash_with_ai_fallback(line);
        }
        
        free(line);
    }
    
    cleanup_and_exit(0);
    return 0;
}
