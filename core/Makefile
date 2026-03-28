CXX = g++

PKG_CONFIG ?= pkg-config
WS2811_CFLAGS := $(shell $(PKG_CONFIG) --cflags libws2811 2>/dev/null)
WS2811_LIBS := $(shell $(PKG_CONFIG) --libs libws2811 2>/dev/null)

ifeq ($(strip $(WS2811_CFLAGS)),)
WS2811_CFLAGS := -I/usr/local/include/ws2811
endif

ifeq ($(strip $(WS2811_LIBS)),)
WS2811_LIBS := -L/usr/local/lib -lws2811
endif

CXXFLAGS = -std=c++17 -Wall -O2 -I./include -pthread $(WS2811_CFLAGS)
LDFLAGS = -pthread $(WS2811_LIBS)

COMMON_SOURCES = src/Display.cpp src/GearPredictor.cpp src/LedStrip.cpp src/ObdReader.cpp
MAIN_SOURCE = src/main.cpp
DEBUG_SOURCE = tools/main_debug.cpp

TARGET = dashboard_app
DEBUG_TARGET = dashboard_debug

all: $(TARGET)

debug: $(DEBUG_TARGET)

$(TARGET): $(COMMON_SOURCES) $(MAIN_SOURCE)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

$(DEBUG_TARGET): $(COMMON_SOURCES) $(DEBUG_SOURCE)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

clean:
	rm -f $(TARGET) $(DEBUG_TARGET)