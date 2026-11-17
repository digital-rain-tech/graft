# FineReport custom functions

Graft generates Java wrappers for `dateToChineseYear`, `dateToChineseMonth`,
`dateToChineseDay`, `numberToChinese`, `decimalToChinese`, and `lastIndexOf`.
The shared numeral/date implementation is `com.fr.function.ChineseTextUtil`.

## Generate outside the repository

After installing Graft, choose an external build directory:

```bash
export GRAFT_FUNCTION_BUILD=/tmp/graft-functions
python - <<'PY'
import os
from pathlib import Path
from graft.translate.finereport_functions import write_custom_functions

for path in write_custom_functions(Path(os.environ["GRAFT_FUNCTION_BUILD"])):
    print(path)
PY
```

This produces seven Java files: the shared helper and six function wrappers.

## Compile and install

Use a JDK and the jars from the FineReport release on the target server. Set
`FR_HOME` to that installation's root, then compile with the package structure:

```bash
mkdir -p "$GRAFT_FUNCTION_BUILD/classes"
javac -encoding UTF-8 -d "$GRAFT_FUNCTION_BUILD/classes" \
  -cp "$FR_HOME/webapps/webroot/WEB-INF/lib/*" \
  "$GRAFT_FUNCTION_BUILD"/*.java
```

Deploy the resulting `classes/com/fr/function/*.class` files into the target
application's `WEB-INF/classes/com/fr/function/` directory. Register each of the six
wrapper classes in the installed release's custom-function manager and reload or
restart the target environment as required by that release. Register the wrappers,
not the shared helper.

Graft's Python tests verify generated source and reference conversion behavior.
They do not compile against proprietary FineReport jars or prove server deployment.
Verify the package, registration procedure, and function results in the target
environment before relying on a converted report.

## Compatibility

The translator recognizes qualified calls using the generic `ChineseTextUtil`
helper and emits bare function calls. Reports using another helper class need
external expression normalization. Existing installations built with a different
shared-helper name need freshly generated, compiled classes; wrapper function
names remain the same. Source-specific mapping/configuration belongs outside the
public source tree.
