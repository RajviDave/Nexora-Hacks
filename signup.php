

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="main-div">
        <form class="form" action="signup.php" method="POST">
            <label><b>Email</b></label><br>
            <input type="text" value="xyz@gmail.com" name="email"><br><br><br>
            <label><b>Username</b></label><br>
            <input type="text" value="Username" name="username"><br><br><br>
            <label><b>Password</b></label><br>
            <input type="password" value="qwertyui" name="passwd"><br><br><br>
            <input type="submit" name="submit" value="SignUp"><br><br>
            <hr>
            <button class="google">SignUp With GOOGLE</button><br><br><br>
        </form>
    </div>
</body>
</html>

<?php
include("db.php");

if($_SERVER["REQUEST_METHOD"] == "POST"){

    $email = htmlspecialchars($_POST["email"]);
    $username = htmlspecialchars($_POST["username"]);
    $password = htmlspecialchars($_POST["passwd"]);

    $hashedPassword = password_hash($password, PASSWORD_DEFAULT);

    // check if email already exists
    $check = $conn->prepare("SELECT id FROM users WHERE email = ?");
    $check->bind_param("s", $email);
    $check->execute();
    $checkResult = $check->get_result();

    if($checkResult->num_rows > 0){
        echo "Email already registered!";
    }
    else{
        // insert user
        $stmt = $conn->prepare("INSERT INTO users (username, email, password) VALUES (?, ?, ?)");
        $stmt->bind_param("sss", $username, $email, $hashedPassword);

        if($stmt->execute()){
            echo "Signup successful ✅";
        }
        else{
            echo "Signup failed ❌";
        }
    }
}
?>
