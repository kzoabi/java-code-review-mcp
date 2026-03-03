package com.example.domain;

import org.pragmatica.lang.Result;
import org.pragmatica.lang.Option;
import java.io.FileReader;

// JBCT-MIX-01: I/O in domain package
// JBCT-EX-01: throws + throw
// JBCT-RET-03: returns null
// JBCT-LAM-01: complex lambda
// JBCT-RET-02: nested wrapper
public class JbctViolations {

    // JBCT-RET-03: returns null
    public String findUser(String id) {
        if (id == null) {
            return null;
        }
        return id;
    }

    // JBCT-EX-01: throws clause
    public void riskyOp() throws RuntimeException {
        throw new RuntimeException("fail");
    }

    // JBCT-RET-02: nested wrapper
    public Result<Option<String>> nested() {
        return Result.success(Option.some("value"));
    }

    // JBCT-MIX-01: I/O in domain
    public void readFile() {
        FileReader reader = null;
    }

    // JBCT-LAM-01: complex lambda with if
    public void processItems(java.util.List<String> items) {
        items.forEach(item -> { if (item != null) { System.out.println(item); } });
    }
}
