# main compiler
CC := gcc

TARGET1 := encoder

all: $(TARGET1)

$(TARGET1): 
	@echo "Compiling C program"
	$(CC) $(CFLAGS) $(TARGET1).c -o $(TARGET1) $(LDFLAGS) 

clean:
	@rm -rf $(TARGET1) $(TARGET2)

