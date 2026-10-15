namespace GitHubCourse.Models;

public sealed class CourseDocument
{
    public string CourseTitle { get; set; } = string.Empty;
    public string CourseSubtitle { get; set; } = string.Empty;
    public List<Lesson> Lessons { get; set; } = [];
}

public sealed class Lesson
{
    public string Id { get; set; } = string.Empty;
    public string Section { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Level { get; set; } = string.Empty;
    public int DurationMinutes { get; set; }
    public string Lead { get; set; } = string.Empty;
    public List<ContentBlock> Blocks { get; set; } = [];
    public LessonDiagram Diagram { get; set; } = new();
    public string Practice { get; set; } = string.Empty;
    public LessonQuiz Quiz { get; set; } = new();
}

public sealed class ContentBlock
{
    public string Type { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
}

public sealed class LessonDiagram
{
    public string Title { get; set; } = string.Empty;
    public string Caption { get; set; } = string.Empty;
    public List<DiagramStep> Steps { get; set; } = [];
}

public sealed class DiagramStep
{
    public string Title { get; set; } = string.Empty;
    public string Detail { get; set; } = string.Empty;
}

public sealed class LessonQuiz
{
    public string Question { get; set; } = string.Empty;
    public List<string> Options { get; set; } = [];
    public int AnswerIndex { get; set; }
    public string Explanation { get; set; } = string.Empty;
}
