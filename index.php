<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log In</title>

    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1 class="heading">SKILL SYNC</h1>
    <div class="main-div">
        <form class="form" action=<?php echo $_SERVER['PHP_SELF'];?> method="post" >
            <label><b>EmailID</b></label><br>
            <input type="text" value="xyz@gmail.com" name="email"><br><br><br>
            <label><b>Password</b></label><br>
            <input type="password" value="qwertyui" name="passwd"><br><br><br>
            <input type="submit" name="submit" value="SignIn"><br><br>
            <hr>
            <button class="google">Signin With GOOGLE</button><br><br><br>
            <label>Don't have account?<a href="signup.php">SIGNUP,</a></label>
        </form>
    </div>
</body>
</html>

<?php
include("db.php");

if($_SERVER["REQUEST_METHOD"] == "POST"){

    $email = $_POST["email"];
    $password = $_POST["passwd"];

    $stmt = $conn->prepare("SELECT * FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();

    $result = $stmt->get_result();

    if($result->num_rows == 1){

        $user = $result->fetch_assoc();

        if(password_verify($password, $user["password"])){
            echo "Login successful ✅";
            // start session / redirect
        } else {
            echo "Wrong password ❌";
        }

    } else {
        echo "User not found ❌";
    }
}
?>
