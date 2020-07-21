CFLAGS = -O3 -Wall -g -lm
TARGET = pigaincorrect

#mkltimdist: /home/yyoshida/Dropbox/Copy/mkltimdist.c
pigaincorrect: pigaincorrect.c
	gcc $^ -o $@ $(CFLAGS)

all: $(TARGET)

clean:
	rm -f $(TARGET)
