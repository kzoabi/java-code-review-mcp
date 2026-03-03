package com.example;

public class EmptyCatch {
    public void doSomething() {
        try {
            riskyOperation();
        } catch (Exception e) {
        }
    }

    private void riskyOperation() throws Exception {}
}
