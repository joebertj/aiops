CC = gcc
CFLAGS = -Wall -Wextra -std=c99
LIBS = -lreadline

TARGET = awesh
SOURCE = awesh.c

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE) $(LIBS)

clean:
	rm -f $(TARGET)

install: $(TARGET)
	cp $(TARGET) /usr/local/bin/
	chmod +x /usr/local/bin/$(TARGET)

.PHONY: all clean install
