<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
session_start();
include("db.php");

if(isset($_SESSION["user_id"])) {
    header("Location: match.php");
    exit();
}

if($_SERVER["REQUEST_METHOD"] == "POST"){

    $email = trim($_POST["email"]);
    $password = $_POST["password"];

    if(!filter_var($email, FILTER_VALIDATE_EMAIL)){
        $error = "Invalid email format ❌";
    }
    else if(strlen($password) < 6){
        $error = "Password must be at least 6 characters ❌";
    }
    else {
        // Check if email already exists
        $stmt = $conn->prepare("SELECT id FROM users WHERE email = ?");
        $stmt->bind_param("s", $email);
        $stmt->execute();
        $result = $stmt->get_result();

        if($result->num_rows > 0){
            $error = "Email already registered ❌";
        } else {

            // Hash password
            $hashed_password = password_hash($password, PASSWORD_DEFAULT);

            // Insert user
            $stmt = $conn->prepare("INSERT INTO users (email, password) VALUES (?, ?)");
            $stmt->bind_param("ss", $email, $hashed_password);

            if($stmt->execute()){
                header("Location: index.php");
                exit();
            } else {
                $error = "Signup failed ❌";
            }
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Signup</title>
</head>
<body>

<h2>Signup</h2>

<?php if(isset($error)) { ?>
    <p style="color:red; font-weight:bold;"><?php echo $error; ?></p>
<?php } ?>

<form method="POST" action="signup.php">
    <label>Email:</label><br>
    <input type="text" name="email" required><br><br>

    <label>Password:</label><br>
    <input type="password" name="password" required><br><br>

    <button type="submit">Signup</button>
</form>

<p>Already have account? <a href="index.php">Login</a></p>

</body>
</html>
