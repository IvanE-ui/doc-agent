$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:5000/")
$listener.Start()

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

while ($listener.IsListening) {
    $ctx  = $listener.GetContext()
    $req  = $ctx.Request
    $res  = $ctx.Response

    $path = $req.Url.LocalPath.TrimStart('/')
    if ($path -eq '' -or $path -eq 'index.html') { $path = 'prototype.html' }

    $file = Join-Path $root $path

    if (Test-Path $file -PathType Leaf) {
        $ext = [System.IO.Path]::GetExtension($file).ToLower()
        $ct  = switch ($ext) {
            '.html' { 'text/html; charset=utf-8' }
            '.js'   { 'application/javascript' }
            '.css'  { 'text/css' }
            default { 'application/octet-stream' }
        }
        $bytes = [System.IO.File]::ReadAllBytes($file)
        $res.ContentType      = $ct
        $res.ContentLength64  = $bytes.LongLength
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
        $msg = [System.Text.Encoding]::UTF8.GetBytes("404 Not found: $path")
        $res.StatusCode      = 404
        $res.ContentLength64 = $msg.LongLength
        $res.OutputStream.Write($msg, 0, $msg.Length)
    }

    $res.OutputStream.Flush()
    $res.OutputStream.Close()
}
