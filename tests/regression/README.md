# tests/regression/

Each test here documents a real bug found in production code. Tests stay
`xfail-strict` until the underlying code is fixed in a Phase 3+ commit, at
which point the `xfail` marker comes off and the test joins the regular
suite. `strict=True` means a fix that accidentally lands without removing
the marker shows up as XPASS → test-suite failure, forcing the operator to
finish the cleanup.
