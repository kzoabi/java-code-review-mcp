// Sample Java file following best practices
public record UserDTO(String name, String email, int age) {
    public static UserDTO create(String name, String email, int age) {
        return new UserDTO(name, email, age);
    }
}

public class GoodCodeExample {
    private static final Logger logger = LoggerFactory.getLogger(GoodCodeExample.class);
    private final String apiKey;
    
    public GoodCodeExample(String apiKey) {
        this.apiKey = Objects.requireNonNull(apiKey, "API key must not be null");
    }
    
    public Optional<String> process(String input) {
        if (input == null || input.isBlank()) {
            return Optional.empty();
        }
        logger.info("Processing input of length: {}", input.length());
        return Optional.of("Processed: " + input);
    }
    
    public record ProcessResult(String status, String message) {
        public static ProcessResult success(String message) {
            return new ProcessResult("SUCCESS", message);
        }
        
        public static ProcessResult error(String message) {
            return new ProcessResult("ERROR", message);
        }
    }
    
    public ProcessResult calculate(int value) {
        return switch (value) {
            case 1 -> ProcessResult.success("One");
            case 2 -> ProcessResult.success("Two");
            case 3 -> ProcessResult.success("Three");
            default -> ProcessResult.error("Unknown value");
        };
    }
    
    public void demonstrateVar() {
        var list = new ArrayList<String>();
        var map = new HashMap<String, Integer>();
    }
}
