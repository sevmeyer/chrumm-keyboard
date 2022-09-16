"""
Generate Chrumm keyboard STL files, based on JSON configuration files.
If a configuration parameter appears multiple times, then its latest
value is used. STL files are written to the working directory.

Usage:
  chrumm [--help] [--version]
         [--log LEVEL] [--threads N]
         [--split] [--knob] JSON...

Options:
  -h, --help   Print this help and exit.
  --version    Print program version and exit.
  --log LEVEL  Either DEBUG, INFO, WARNING, or ERROR (default: INFO).
  --threads N  Number of threads to use (default: 8).
  --split      Split into halves for smaller printbeds.
  --knob       Generate the encoder knob only.
"""

import getopt
import json
import logging
import pathlib
import sys
import time
import traceback

import chrumm


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger()


def main():
    try:
        threads = 8
        isSplit = False
        isKnob = False

        options, jsonFiles = getopt.getopt(
            sys.argv[1:], "h", "help version log= threads= split knob".split())

        for name, arg in options:
            if name == "-h" or name == "--help":
                print(__doc__)
                sys.exit(0)
            elif name == "--version":
                print(chrumm.__version__)
                sys.exit(0)
            elif name == "--log":
                logging.getLogger().setLevel(arg)
            elif name == "--threads":
                threads = int(arg)
            elif name == "--split":
                isSplit = True
            elif name == "--knob":
                isKnob = True

        if not jsonFiles:
            raise getopt.GetoptError("Missing JSON argument.")

        jsonPaths = [pathlib.Path(f) for f in jsonFiles]
        jsonStrings = [p.read_text() for p in jsonPaths]
        jsonStem = jsonPaths[-1].stem

        log.info("This is chrumm %s", chrumm.__version__,)
        log.info(r"  ___ _   _ ____  _   _ _    _ _    _ ")
        log.info(r".' __| |_| |  _ '| | | | \  / | \  / |")
        log.info(r"| |__|  _  | |_) | |_| |  \/  |  \/  |")
        log.info(r"'.___|_| |_|_| \_\.___.|_|\/|_|_|\/|_|")
        log.info("")

        seconds = time.perf_counter()
        stls = chrumm.make(jsonStrings, threads, isSplit, isKnob)

        for name, stl in stls.items():
            path = pathlib.Path(f"{jsonStem}-{name}.stl")
            log.info('Writing "%s"...', path)
            path.write_bytes(stl)

        seconds = time.perf_counter() - seconds
        log.info("Done after %.3f seconds.", seconds)

    except json.decoder.JSONDecodeError as e:
        log.error("Could not parse JSON: %s", e)
        log.debug(traceback.format_exc().strip())
        sys.exit(1)

    except ZeroDivisionError:
        log.error(
            "Encountered a division by zero.\n"
            "  This can be caused by overlapping points or malformed geometry.\n"
            "  Make sure to use sensible parameters, especially for margins and chamfers.")
        log.debug(traceback.format_exc().strip())
        sys.exit(1)

    except Exception as e:
        log.error(e)
        log.debug(traceback.format_exc().strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
