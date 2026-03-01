// Sample Java file with various issues for testing
public class BadCodeExample {
    private String password = "hardcoded_password";
    private static final int MAGIC_NUMBER = 999;
    
    public String process(String input) {
        System.out.println("Processing: " + input);
        try {
            String query = "SELECT * FROM users WHERE name = '" + input + "'";
            executeQuery(query);
        } catch (Exception e) {
        }
        return "Result: " + input;
    }
    
    public void executeQuery(String sql) {
    }
    
    public void longMethodWithTooManyParams(String a, String b, String c, String d, String e, String f) {
        String result = "";
        for (int i = 0; i < 100; i++) {
            result += "item" + i;
        }
    }
    
    public int calculate(int x, int y, int z, int w, int v, int u) {
        if (x == 1) {
            return 1;
        } else if (x == 2) {
            return 2;
        } else if (x == 3) {
            return 3;
        } else if (x == 4) {
            return 4;
        } else if (x == 5) {
            return 5;
        } else {
            return 0;
        }
    }
}
