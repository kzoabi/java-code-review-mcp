package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.GetMapping;

// Field injection — should trigger SPRING-DI-01
@Service
public class SpringIssues {

    @Autowired
    private UserRepository userRepository;

    // @Transactional on private method — should trigger SPRING-TX-01
    @Transactional
    private void saveUser(String name) {
        userRepository.save(name);
    }

    // @Value with hardcoded fallback — should trigger SPRING-CONFIG-01
    @Value("${app.timeout:30}")
    private int timeout;
}

// @RestController returning raw String instead of ResponseEntity
@RestController
class UserController {
    @GetMapping("/users")
    public String getUsers() {
        return "[]";
    }
}

interface UserRepository {
    void save(String name);
}
