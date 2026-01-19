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

    $stmt = $conn->prepare("SELECT id, email, password FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();

    $result = $stmt->get_result();

    if($result->num_rows == 1){

        $user = $result->fetch_assoc();

        if(password_verify($password, $user["password"])){

            $_SESSION["user_id"] = $user["id"];
            $_SESSION["email"] = $user["email"];

            header("Location: match.php");
            exit();

        } else {
            $error = "Wrong password ❌";
        }

    } else {
        $error = "User not found ❌";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>

<h2>Login</h2>

<?php if(isset($error)) { ?>
    <p style="color:red; font-weight:bold;"><?php echo $error; ?></p>
<?php } ?>

<form method="POST" action="index.php">
    <label>Email:</label><br>
    <input type="text" name="email" required><br><br>

    <label>Password:</label><br>
    <input type="password" name="password" required><br><br>

    <button type="submit">Login</button>
</form>

<p>Don't have account? <a href="signup.php">Signup</a></p>

</body>
</html>
