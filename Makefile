# Harris ModPack. Run `make` to see the commands.
PY ?= python3
PACK := pack

.PHONY: help install update test check olly mod art pixelize refresh export server outdated tools clean

help:
	@echo "make install    install/update the Prism instance (same as ./install.sh --no-open)"
	@echo "make test       boot the real game into a test world and check everything loads"
	@echo "make check      fast static checks (hashes, Olly jar, sides)"
	@echo "make olly       rebuild the Olly mod jar after editing olly/"
	@echo "make mod        build the Harris Java mod (mod/) into the pack"
	@echo "make art        render art/*.txt pixel art into textures"
	@echo "make pixelize IN=pic.png NAME=item_name   turn any image (a drawing, a photo) into a 16x16 item texture"
	@echo "make outdated   list mods with newer versions on Modrinth"
	@echo "make update     update every mod to its newest version (review, then make test)"
	@echo "make export     build dist/Harris-ModPack-<version>.mrpack for friends"
	@echo "make server DIR=~/mc-server   set up a dedicated server"
	@echo "make tools      install packwiz (needed to add/update mods)"

install:
	./install.sh --no-open

test:
	$(PY) scripts/smoke_test.py

check:
	$(PY) scripts/modpack.py check

olly:
	$(PY) scripts/modpack.py build-olly

VENV := .venv
$(VENV)/bin/python:
	$(PY) -m venv $(VENV) && $(VENV)/bin/pip install -q pillow

pixelize: $(VENV)/bin/python
	@test -n "$(IN)" -a -n "$(NAME)" || (echo "usage: make pixelize IN=picture.png NAME=item_name [ARGS='--colors 10 --outline']" && exit 1)
	$(VENV)/bin/python scripts/pixelize.py "$(IN)" mod/src/main/resources/assets/harris/textures/item/$(NAME).png $(ARGS)

art:
	$(PY) scripts/pixelart.py

# Builds mod/ with Gradle (Java 21) and drops the jar into the pack.
mod: art
	cd mod && JAVA_HOME=$$(brew --prefix openjdk@21) ./gradlew build --console=plain -q
	rm -f $(PACK)/mods/harris-*.jar
	cp mod/build/libs/harris-*.jar $(PACK)/mods/
	cd $(PACK) && packwiz refresh

refresh:
	cd $(PACK) && packwiz refresh

outdated:
	cd $(PACK) && printf 'n\n' | packwiz update --all || true

update:
	cd $(PACK) && packwiz update --all -y

export:
	$(PY) scripts/modpack.py export

server:
	@test -n "$(DIR)" || (echo "usage: make server DIR=/path/to/server" && exit 1)
	$(PY) scripts/modpack.py server "$(DIR)"

tools:
	brew list go >/dev/null 2>&1 || brew install go
	GOBIN=$$(brew --prefix)/bin go install github.com/packwiz/packwiz@latest

clean:
	rm -rf dist .test/client
