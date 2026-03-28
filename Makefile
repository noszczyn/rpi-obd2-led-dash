.PHONY: all debug clean

all:
	$(MAKE) -C core all

debug:
	$(MAKE) -C core debug

clean:
	$(MAKE) -C core clean
