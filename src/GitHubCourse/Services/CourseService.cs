using System.IO;
using System.Reflection;
using System.Text.Json;
using GitHubCourse.Models;

namespace GitHubCourse.Services;

public static class CourseService
{
    private const string CourseResourceName = "GitHubCourse.Course.lessons.json";

    public static CourseDocument Load()
    {
        using Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(CourseResourceName)
            ?? throw new InvalidOperationException($"В сборку не включён ресурс курса: {CourseResourceName}");

        CourseDocument? course = JsonSerializer.Deserialize<CourseDocument>(stream, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });

        if (course is null || course.Lessons.Count == 0)
        {
            throw new InvalidOperationException("Файл курса пуст или имеет неверный формат.");
        }

        return course;
    }
}
