CC = gcc
CFLAGS = -Wall -Wextra -std=c99
LIBS = -lreadline

TARGET = awesh
SOURCE = awesh.c
BACKEND_PKG = ../awesh_backend

all: $(TARGET) backend

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE) $(LIBS)

backend:
	@echo "Backend package ready at $(BACKEND_PKG)"

clean:
	rm -f $(TARGET)

install: $(TARGET) backend
	@echo "Installing awesh to ~/.local/bin..."
	mkdir -p ~/.local/bin
	cp $(TARGET) ~/.local/bin/
	@echo "Installing Python backend package..."
	cd .. && pip install -e .
	@echo "✅ awesh installation complete!"
	@echo "Run 'awesh' from anywhere to start the shell"

install-system: $(TARGET) backend
	@echo "Installing awesh system-wide..."
	sudo cp $(TARGET) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(TARGET)
	cd .. && sudo pip install -e .
	@echo "✅ awesh installed system-wide!"

uninstall:
	@echo "Uninstalling awesh..."
	rm -f ~/.local/bin/$(TARGET)
	pip uninstall -y awesh-backend
	@echo "✅ awesh uninstalled"

.PHONY: all clean install install-system uninstall backend
