CFLAGS = -O3 -Wall -Wno-unused-result -g -lm 
TARGET = pigaincorrect

pigaincorrect: src/pigaincorrect/pigaincorrect.c
	gcc $^ -o $@ $(CFLAGS)

all: $(TARGET)

clean:
	rm -f $(TARGET)
