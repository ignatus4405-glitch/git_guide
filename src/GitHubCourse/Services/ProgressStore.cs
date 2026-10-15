using System.Text.Json;

namespace GitHubCourse.Services;

public sealed class ProgressStore
{
    private readonly string _progressPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "GitHubCourse",
        "progress.json");

    public HashSet<string> Load()
    {
        try
        {
            if (!File.Exists(_progressPath))
            {
                return new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            }

            string[]? saved = JsonSerializer.Deserialize<string[]>(File.ReadAllText(_progressPath));
            return new HashSet<string>(saved ?? [], StringComparer.OrdinalIgnoreCase);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException)
        {
            // A damaged progress file should not prevent the course from opening.
            return new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        }
    }

    public void Save(IEnumerable<string> completedLessonIds)
    {
        string directory = Path.GetDirectoryName(_progressPath)!;
        Directory.CreateDirectory(directory);

        string temporaryPath = _progressPath + ".tmp";
        try
        {
            string json = JsonSerializer.Serialize(completedLessonIds.Order(StringComparer.OrdinalIgnoreCase));
            File.WriteAllText(temporaryPath, json);
            File.Move(temporaryPath, _progressPath, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }
}
