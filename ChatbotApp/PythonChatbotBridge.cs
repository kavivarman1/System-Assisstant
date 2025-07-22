using System;
using System.Diagnostics;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Net.Sockets;

public class PythonChatbotBridge : IDisposable
{
    private readonly HttpClient httpClient;
    private readonly string serverUrl = "http://127.0.0.1:5005/chat";
    private Process backendProcess;

    public PythonChatbotBridge()
    {
        httpClient = new HttpClient();
        EnsureBackendRunning();
    }

    private void EnsureBackendRunning()
    {
        if (!IsBackendAvailable())
        {
            // Adjust the path to your Python executable and script as needed
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = "smart_chatbot.py",
                WorkingDirectory = AppDomain.CurrentDomain.BaseDirectory,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            backendProcess = Process.Start(psi);
            // Optionally, wait a few seconds for the server to start
            Task.Delay(2000).Wait();
        }
    }

    private bool IsBackendAvailable()
    {
        try
        {
            using (var client = new TcpClient())
            {
                var result = client.BeginConnect("127.0.0.1", 5005, null, null);
                var success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(500));
                return success && client.Connected;
            }
        }
        catch
        {
            return false;
        }
    }

    public async Task<string> SendMessageAsync(string message)
    {
        var json = $"{{\"message\": \"{EscapeJson(message)}\"}}";
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        try
        {
            var response = await httpClient.PostAsync(serverUrl, content);
            response.EnsureSuccessStatusCode();
            var responseString = await response.Content.ReadAsStringAsync();
            return responseString;
        }
        catch (Exception ex)
        {
            return $"[Error communicating with backend: {ex.Message}]";
        }
    }

    private string EscapeJson(string s)
    {
        return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r");
    }

    public void Dispose()
    {
        httpClient?.Dispose();
        if (backendProcess != null && !backendProcess.HasExited)
            backendProcess.Kill();
        backendProcess?.Dispose();
    }
}