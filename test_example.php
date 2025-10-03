<?php

/**
 * Example usage of the Excel to CSV conversion API
 * This file demonstrates how to use the LibreOffice conversion service
 */

// Example 1: Convert Excel file from base64 data
function testExcelConversion()
{
    $url = 'http://localhost:8080';

    $excelData = base64_encode(file_get_contents('./tmp/__TEST__FILE__.xlsx'));

    $data = [
        'excelData' => $excelData,
        'params' => [
            'format' => 'xlsx' // or 'xls', 'xlsm'
        ],
        'output' => 'converted_file.csv',
        'debug' => true
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode === 200) {
        // Save the CSV response
        file_put_contents('output.csv', $response);
        echo "Conversion successful! CSV saved as output.csv\n";
    } else {
        echo "Error: " . $response . "\n";
    }
}

// Example 2: Convert Excel file from file path
function testExcelFileConversion()
{
    $url = 'http://localhost:8080';

    $data = [
        'excel' => './tmp/__TEST__FILE__.xlsx',
        'output' => 'converted_file.csv'
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode === 200) {
        file_put_contents('output.csv', $response);
        echo "Conversion successful! CSV saved as output.csv\n";
    } else {
        echo "Error: " . $response . "\n";
    }
}

echo "Excel to CSV Conversion API Examples\n";
echo "====================================\n\n";

echo "To test the API, you can use one of these methods:\n";
echo "1. Send Excel file as base64 data in 'excelData' field\n";
echo "2. Provide file path in 'excel' field (file must exist on server)\n\n";

echo "Example JSON request:\n";
echo json_encode([
    'excelData' => 'base64_encoded_excel_content_here',
    'params' => [
        'format' => 'xlsx'
    ],
    'output' => 'converted_file.csv',
    'debug' => true
], JSON_PRETTY_PRINT);

echo "\n\nSupported Excel formats: xlsx, xls, xlsm\n";
echo "Output format: CSV\n";
echo "API endpoint: POST / (root)\n";
echo "Content-Type: application/json\n";

