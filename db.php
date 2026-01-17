<?php
    $host="localhost";
    $user="root";
    $pass="";
    $db="SkillSync";

    $conn=new mysqli($host,$user,$pass,$db);

    if($conn->connect_error){
        echo "Database connnection fail".$conn->connect_error;
    }else{
        echo "Database Connected successfully";
    }

    $conn->set_charset("utf8");
?>