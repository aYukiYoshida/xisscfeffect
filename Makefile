CFLAGS = -O3 -Wall -g -lm
TARGET = pigaincorrect

pigaincorrect: pigaincorrect.c
	gcc $^ -o $@ $(CFLAGS)

all: $(TARGET)

clean:
	rm -f $(TARGET)
