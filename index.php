<?php

set_time_limit(getenv('MAX_EXECUTION_TIME') ?? 300);
ignore_user_abort(true);

function generateTempFile($content = null, $ext = 'html')
{
    $tmpName = tempnam(sys_get_temp_dir(), $ext) . '.' . $ext;
    if ($content)
        file_put_contents($tmpName, $content);

    return $tmpName;
}

header('Content-Type: application/json');

// Accept only POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Only POST allowed']);
    exit;
}

// Read JSON input
$input = json_decode(file_get_contents('php://input'), true);

$procNum = rand(1000, 9999);
$excelFile = $input['excel'] ?? null;
$excelData = $input['excelData'] ?? null;
$params = $input['params'] ?? [];
$output = !empty($input['output']) ? "/app/output/{$input['output']}" : null;

$uri = strtolower(trim($_SERVER['REQUEST_URI'], '/'));

if (!$excelFile && !$excelData) {
    http_response_code(400);
    echo json_encode(['error' => 'Either "excel" (file path) or "excelData" (base64 encoded data) must be provided']);
    exit;
}

$tmpFile = [];
$tmpFile['output'] = generateTempFile(null, 'csv');

// Handle Excel file input
if ($excelData) {
    // Decode base64 data
    $excelContent = base64_decode($excelData);
    if ($excelContent === false) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid base64 data']);
        exit;
    }

    // Determine file extension based on content or params
    $ext = $params['format'] ?? 'xlsx';
    if (!in_array($ext, ['xlsx', 'xls', 'xlsm'])) {
        $ext = 'xlsx';
    }

    $tmpFile['input'] = generateTempFile($excelContent, $ext);
} else {
    // Use provided file path
    $tmpFile['input'] = $excelFile;
}

try {
    error_log(date('[H:i:s] ') . "{$procNum}- New request: converting Excel to CSV");

    // LibreOffice command to convert Excel to CSV
    $cmd = [
        'libreoffice',
        '--headless',
        '--convert-to',
        'csv:Text - txt - csv (StarCalc):44,34,76,1',
        '--outdir',
        dirname($tmpFile['output']),
        $tmpFile['input']
    ];

    error_log(date('[H:i:s] ') . "{$procNum}- Process started");
    if ($input['debug'] ?? false)
        file_put_contents('doc.sh', implode(' ', $cmd));

    // Open process
    $descriptors = [
        0 => ['pipe', 'r'], // stdin
        1 => ['pipe', 'w'], // stdout
        2 => ['pipe', 'w'], // stderr
    ];

    $process = proc_open($cmd, $descriptors, $pipes);

    if (!is_resource($process)) {
        throw new RuntimeException('Could not open LibreOffice process');
    }

    // Capture error (if any)
    $stderr = stream_get_contents($pipes[2]);
    fclose($pipes[2]);

    // Wait for process to finish
    $status = proc_close($process);

    if ($status !== 0) {
        throw new RuntimeException("Excel to CSV conversion failed: $stderr");
    }

    // Find the generated CSV file (LibreOffice creates it with the same name as input)
    $inputBasename = pathinfo($tmpFile['input'], PATHINFO_FILENAME);
    $generatedCsv = dirname($tmpFile['output']) . '/' . $inputBasename . '.csv';

    if (!file_exists($generatedCsv)) {
        throw new RuntimeException("CSV file was not generated");
    }

    // Move to our output location
    rename($generatedCsv, $tmpFile['output']);

    // Serve generated CSV
    header('Content-Type: text/csv');
    header('Content-Disposition: inline; filename="output.csv"');

    error_log(date('[H:i:s] ') . "{$procNum}- Process ended");

    // copy to output
    if ($output && !file_exists($output)) {
        copy($tmpFile['output'], $output);
        error_log(date('[H:i:s] ') . "{$procNum}- Output created: {$output}");
    } else {
        readfile($tmpFile['output']);
    }

    error_log(date('[H:i:s] ') . "{$procNum}- Output sent");
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'error' => $e->getMessage(),
        'cmd' => implode(' ', $cmd ?? []),
    ]);
    error_log(date('[H:i:s] ') . "{$procNum}- ERROR " . $e->getMessage());
} finally {
    // cleanup
    foreach ($tmpFile as $tmp) {
        if (file_exists($tmp)) {
            unlink($tmp);
        }
    }
}

error_log(date('[H:i:s] ') . "{$procNum}- Finished");
