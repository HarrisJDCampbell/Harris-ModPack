# Harris ModPack. Run `make` to see the commands.
PY ?= python3
PACK := pack

.PHONY: help install update test check olly refresh export server outdated tools clean

help:
	@echo "make install    install/update the Prism instance (same as ./install.sh --no-open)"
	@echo "make test       boot the real game into a test world and check everything loads"
	@echo "make check      fast static checks (hashes, Olly jar, sides)"
	@echo "make olly       rebuild the Olly mod jar after editing olly/"
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
