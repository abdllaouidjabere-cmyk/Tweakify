<?php
// CORS headers - allow requests from same origin
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Only allow POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Read JSON data from the request body
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$name    = trim($data['name']    ?? '');
$phone   = trim($data['phone']   ?? '');
$email   = trim($data['email']   ?? '');
$country = trim($data['country'] ?? '');

if (!$name || !$phone || !$email || !$country) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

try {
    // Use absolute path so SQLite works on any hosting
    $dbPath = __DIR__ . '/users.db';
    $db = new PDO('sqlite:' . $dbPath);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Create table if not exists
    $db->exec("CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        phone      TEXT NOT NULL,
        email      TEXT NOT NULL,
        country    TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )");

    // Insert user
    $stmt = $db->prepare("INSERT INTO users (name, phone, email, country)
                          VALUES (:name, :phone, :email, :country)");
    $stmt->bindValue(':name',    $name);
    $stmt->bindValue(':phone',   $phone);
    $stmt->bindValue(':email',   $email);
    $stmt->bindValue(':country', $country);
    $stmt->execute();

    echo json_encode(['success' => true, 'message' => 'Registration successful']);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
