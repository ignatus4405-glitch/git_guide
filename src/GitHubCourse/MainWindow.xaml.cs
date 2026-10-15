using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using GitHubCourse.Models;
using GitHubCourse.Services;

namespace GitHubCourse;

public partial class MainWindow : Window
{
    private readonly ProgressStore _progressStore = new();
    private readonly HashSet<string> _completedLessonIds;
    private CourseDocument _course;
    private int _currentLessonIndex;
    private int? _selectedQuizAnswer;
    private TextBlock? _quizFeedback;
    private Button? _completionButton;

    public MainWindow()
    {
        InitializeComponent();

        try
        {
            _course = CourseService.Load();
            _completedLessonIds = _progressStore.Load();
            _completedLessonIds.RemoveWhere(id => _course.Lessons.All(lesson => lesson.Id != id));

            HeaderCourseTitle.Text = _course.CourseTitle;
            HeaderCourseSubtitle.Text = _course.CourseSubtitle;
            Title = $"{_course.CourseTitle} — Windows";
            UpdateCourseProgress();
            BuildNavigation();
            RenderLesson(0);
        }
        catch (Exception exception)
        {
            MessageBox.Show(
                $"Не удалось открыть курс. Проверьте, что lessons.json включён в сборку.\n\n{exception.Message}",
                "Ошибка загрузки курса",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            Close();
            _course = new CourseDocument();
            _completedLessonIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        }
    }

    private void SearchBox_OnTextChanged(object sender, TextChangedEventArgs e)
    {
        SearchPlaceholder.Visibility = string.IsNullOrEmpty(SearchBox.Text) ? Visibility.Visible : Visibility.Collapsed;
        if (_course is not null && _course.Lessons.Count > 0)
        {
            BuildNavigation();
        }
    }

    private void BuildNavigation()
    {
        LessonNavigation.Children.Clear();
        string search = SearchBox.Text.Trim();
        string previousSection = string.Empty;

        for (int index = 0; index < _course.Lessons.Count; index++)
        {
            Lesson lesson = _course.Lessons[index];
            if (!string.IsNullOrWhiteSpace(search)
                && !lesson.Title.Contains(search, StringComparison.CurrentCultureIgnoreCase)
                && !lesson.Section.Contains(search, StringComparison.CurrentCultureIgnoreCase))
            {
                continue;
            }

            if (!string.Equals(previousSection, lesson.Section, StringComparison.Ordinal))
            {
                previousSection = lesson.Section;
                LessonNavigation.Children.Add(new TextBlock
                {
                    Text = lesson.Section.ToUpperInvariant(),
                    Foreground = new SolidColorBrush(Color.FromRgb(112, 131, 157)),
                    FontSize = 9,
                    FontWeight = FontWeights.Bold,
                    Margin = new Thickness(3, 10, 0, 6)
                });
            }

            bool isActive = index == _currentLessonIndex;
            bool isComplete = _completedLessonIds.Contains(lesson.Id);
            var title = new TextBlock
            {
                Text = $"{(isComplete ? "✓" : (index + 1).ToString("D2"))}  {lesson.Title}",
                Foreground = isActive ? Brushes.White : new SolidColorBrush(Color.FromRgb(209, 219, 233)),
                FontSize = 12,
                FontWeight = isActive ? FontWeights.SemiBold : FontWeights.Normal,
                TextWrapping = TextWrapping.Wrap
            };
            var meta = new TextBlock
            {
                Text = $"{lesson.Level} · {lesson.DurationMinutes} мин",
                Foreground = new SolidColorBrush(Color.FromRgb(137, 154, 177)),
                FontSize = 10,
                Margin = new Thickness(24, 4, 0, 0)
            };
            var content = new StackPanel();
            content.Children.Add(title);
            content.Children.Add(meta);

            var button = new Button
            {
                Content = content,
                Tag = lesson.Id,
                Style = (Style)FindResource("NavigationButtonStyle"),
                Background = isActive ? new SolidColorBrush(Color.FromRgb(36, 54, 79)) : Brushes.Transparent,
                Margin = new Thickness(0, 1, 0, 1)
            };
            button.Click += NavigationButton_OnClick;
            LessonNavigation.Children.Add(button);
        }

        if (LessonNavigation.Children.Count == 0)
        {
            LessonNavigation.Children.Add(new TextBlock
            {
                Text = "Ничего не найдено. Попробуйте другое слово.",
                Foreground = new SolidColorBrush(Color.FromRgb(169, 183, 203)),
                TextWrapping = TextWrapping.Wrap,
                FontSize = 12,
                Margin = new Thickness(4, 8, 4, 0)
            });
        }
    }

    private void NavigationButton_OnClick(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string lessonId })
        {
            return;
        }

        int index = _course.Lessons.FindIndex(lesson => lesson.Id == lessonId);
        if (index >= 0)
        {
            RenderLesson(index);
        }
    }

    private void RenderLesson(int index)
    {
        if (_course.Lessons.Count == 0)
        {
            return;
        }

        _currentLessonIndex = Math.Clamp(index, 0, _course.Lessons.Count - 1);
        Lesson lesson = _course.Lessons[_currentLessonIndex];
        _selectedQuizAnswer = null;
        _quizFeedback = null;
        _completionButton = null;
        LessonScrollViewer.ScrollToTop();
        LessonContent.Children.Clear();

        LessonContent.Children.Add(CreateHero(lesson, _currentLessonIndex));
        LessonContent.Children.Add(CreateDiagram(lesson.Diagram));

        foreach (ContentBlock block in lesson.Blocks)
        {
            UIElement? element = CreateContentBlock(block);
            if (element is not null)
            {
                LessonContent.Children.Add(element);
            }
        }

        LessonContent.Children.Add(CreatePractice(lesson.Practice));
        LessonContent.Children.Add(CreateQuiz(lesson));
        LessonContent.Children.Add(CreateLessonFooter(_currentLessonIndex));

        BuildNavigation();
        UpdateCompletionButton();
    }

    private UIElement CreateHero(Lesson lesson, int index)
    {
        var body = new StackPanel();
        var labels = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 15) };
        labels.Children.Add(CreatePill(lesson.Section, "#EAF0FF", "#3B62B6"));
        labels.Children.Add(CreatePill($"УРОК {index + 1:00} ИЗ {_course.Lessons.Count:00}", "#F1F4F8", "#566579", 8));
        labels.Children.Add(CreatePill($"{lesson.DurationMinutes} МИН", "#F1F4F8", "#566579", 8));
        body.Children.Add(labels);
        body.Children.Add(new TextBlock
        {
            Text = lesson.Title,
            FontSize = 31,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(25, 37, 55)),
            TextWrapping = TextWrapping.Wrap,
            LineHeight = 39,
            Margin = new Thickness(0, 0, 0, 12)
        });
        body.Children.Add(new TextBlock
        {
            Text = lesson.Lead,
            FontSize = 15,
            Foreground = new SolidColorBrush(Color.FromRgb(86, 101, 122)),
            TextWrapping = TextWrapping.Wrap,
            LineHeight = 25
        });

        return new Border
        {
            Background = Brushes.White,
            CornerRadius = new CornerRadius(18),
            Padding = new Thickness(28, 25, 28, 27),
            Margin = new Thickness(0, 0, 0, 18),
            Child = body
        };
    }

    private static Border CreatePill(string text, string background, string foreground, double leftMargin = 0)
    {
        return new Border
        {
            Background = (Brush)new BrushConverter().ConvertFromString(background)!,
            CornerRadius = new CornerRadius(7),
            Padding = new Thickness(9, 6, 9, 6),
            Margin = new Thickness(leftMargin, 0, 7, 0),
            Child = new TextBlock
            {
                Text = text,
                Foreground = (Brush)new BrushConverter().ConvertFromString(foreground)!,
                FontSize = 9,
                FontWeight = FontWeights.Bold
            }
        };
    }

    private static UIElement CreateDiagram(LessonDiagram diagram)
    {
        var stack = new StackPanel();
        stack.Children.Add(new TextBlock
        {
            Text = diagram.Title,
            FontSize = 15,
            FontWeight = FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Color.FromRgb(36, 51, 72)),
            Margin = new Thickness(0, 0, 0, 5)
        });
        stack.Children.Add(new TextBlock
        {
            Text = diagram.Caption,
            FontSize = 12,
            Foreground = new SolidColorBrush(Color.FromRgb(112, 127, 148)),
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, 0, 0, 15)
        });

        var flow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Stretch };
        for (int index = 0; index < diagram.Steps.Count; index++)
        {
            DiagramStep step = diagram.Steps[index];
            var cardContent = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            cardContent.Children.Add(new TextBlock
            {
                Text = step.Title,
                FontSize = 12,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(Color.FromRgb(40, 62, 99)),
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 5)
            });
            cardContent.Children.Add(new TextBlock
            {
                Text = step.Detail,
                FontSize = 10,
                Foreground = new SolidColorBrush(Color.FromRgb(95, 112, 135)),
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 15
            });
            flow.Children.Add(new Border
            {
                Width = 166,
                MinHeight = 76,
                Background = index == 0
                    ? new SolidColorBrush(Color.FromRgb(232, 240, 255))
                    : new SolidColorBrush(Color.FromRgb(247, 249, 252)),
                BorderBrush = index == 0
                    ? new SolidColorBrush(Color.FromRgb(210, 224, 252))
                    : new SolidColorBrush(Color.FromRgb(232, 237, 244)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(12),
                Child = cardContent
            });

            if (index < diagram.Steps.Count - 1)
            {
                flow.Children.Add(new TextBlock
                {
                    Text = "›",
                    FontSize = 30,
                    FontWeight = FontWeights.Light,
                    Foreground = new SolidColorBrush(Color.FromRgb(133, 151, 177)),
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(7, 0, 7, 4)
                });
            }
        }

        stack.Children.Add(new ScrollViewer
        {
            Content = flow,
            HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
            VerticalScrollBarVisibility = ScrollBarVisibility.Disabled,
            Padding = new Thickness(0, 0, 0, 6)
        });

        return new Border
        {
            Background = Brushes.White,
            CornerRadius = new CornerRadius(16),
            Padding = new Thickness(23, 20, 23, 14),
            Margin = new Thickness(0, 0, 0, 21),
            Child = stack
        };
    }

    private static UIElement? CreateContentBlock(ContentBlock block)
    {
        switch (block.Type.Trim().ToLowerInvariant())
        {
            case "heading":
                return new TextBlock
                {
                    Text = block.Text,
                    FontSize = 20,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(Color.FromRgb(32, 46, 66)),
                    TextWrapping = TextWrapping.Wrap,
                    Margin = new Thickness(2, 12, 0, 7)
                };

            case "text":
            case "paragraph":
                return new TextBlock
                {
                    Text = block.Text,
                    FontSize = 14,
                    Foreground = new SolidColorBrush(Color.FromRgb(64, 78, 98)),
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 24,
                    Margin = new Thickness(2, 4, 2, 10)
                };

            case "bullet":
                var bulletContent = new StackPanel { Orientation = Orientation.Horizontal };
                bulletContent.Children.Add(new TextBlock
                {
                    Text = "•",
                    Foreground = new SolidColorBrush(Color.FromRgb(79, 125, 243)),
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Margin = new Thickness(0, -2, 10, 0)
                });
                bulletContent.Children.Add(new TextBlock
                {
                    Text = block.Text,
                    FontSize = 14,
                    Foreground = new SolidColorBrush(Color.FromRgb(64, 78, 98)),
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 23
                });
                return new Border
                {
                    Margin = new Thickness(10, 1, 4, 7),
                    Child = bulletContent
                };

            case "code":
                var codePanel = new StackPanel();
                if (!string.IsNullOrWhiteSpace(block.Title))
                {
                    codePanel.Children.Add(new TextBlock
                    {
                        Text = block.Title,
                        FontSize = 10,
                        FontWeight = FontWeights.Bold,
                        Foreground = new SolidColorBrush(Color.FromRgb(143, 178, 255)),
                        Margin = new Thickness(0, 0, 0, 8)
                    });
                }
                codePanel.Children.Add(new TextBlock
                {
                    Text = block.Text,
                    FontFamily = new FontFamily("Consolas"),
                    FontSize = 12,
                    Foreground = new SolidColorBrush(Color.FromRgb(229, 235, 245)),
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 20
                });
                return new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(19, 29, 45)),
                    CornerRadius = new CornerRadius(11),
                    Padding = new Thickness(18, 15, 18, 16),
                    Margin = new Thickness(0, 5, 0, 13),
                    Child = codePanel
                };

            case "note":
                var noteContent = new StackPanel();
                noteContent.Children.Add(new TextBlock
                {
                    Text = string.IsNullOrWhiteSpace(block.Title) ? "Важно" : block.Title,
                    FontSize = 12,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(Color.FromRgb(53, 86, 151)),
                    Margin = new Thickness(0, 0, 0, 4)
                });
                noteContent.Children.Add(new TextBlock
                {
                    Text = block.Text,
                    FontSize = 13,
                    Foreground = new SolidColorBrush(Color.FromRgb(62, 81, 112)),
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 21
                });
                return new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(237, 244, 255)),
                    BorderBrush = new SolidColorBrush(Color.FromRgb(220, 232, 255)),
                    BorderThickness = new Thickness(1, 0, 0, 0),
                    CornerRadius = new CornerRadius(7),
                    Padding = new Thickness(15, 12, 16, 13),
                    Margin = new Thickness(0, 5, 0, 12),
                    Child = noteContent
                };

            default:
                return new TextBlock
                {
                    Text = block.Text,
                    FontSize = 14,
                    Foreground = Brushes.DarkRed,
                    TextWrapping = TextWrapping.Wrap,
                    Margin = new Thickness(0, 4, 0, 8)
                };
        }
    }

    private static UIElement CreatePractice(string practice)
    {
        var content = new StackPanel();
        content.Children.Add(new TextBlock
        {
            Text = "ПОПРОБУЙТЕ САМИ",
            FontSize = 10,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(50, 111, 92)),
            Margin = new Thickness(0, 0, 0, 7)
        });
        content.Children.Add(new TextBlock
        {
            Text = practice,
            FontSize = 13,
            Foreground = new SolidColorBrush(Color.FromRgb(49, 79, 70)),
            TextWrapping = TextWrapping.Wrap,
            LineHeight = 22
        });
        return new Border
        {
            Background = new SolidColorBrush(Color.FromRgb(233, 248, 241)),
            CornerRadius = new CornerRadius(12),
            Padding = new Thickness(18, 15, 19, 16),
            Margin = new Thickness(0, 13, 0, 20),
            Child = content
        };
    }

    private UIElement CreateQuiz(Lesson lesson)
    {
        var content = new StackPanel();
        content.Children.Add(new TextBlock
        {
            Text = "ПРОВЕРЬТЕ СЕБЯ",
            FontSize = 10,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(86, 111, 161)),
            Margin = new Thickness(0, 0, 0, 7)
        });
        content.Children.Add(new TextBlock
        {
            Text = lesson.Quiz.Question,
            FontSize = 16,
            FontWeight = FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Color.FromRgb(32, 46, 66)),
            TextWrapping = TextWrapping.Wrap,
            LineHeight = 23,
            Margin = new Thickness(0, 0, 0, 11)
        });

        for (int index = 0; index < lesson.Quiz.Options.Count; index++)
        {
            int optionIndex = index;
            var option = new RadioButton
            {
                Content = lesson.Quiz.Options[index],
                GroupName = $"quiz-{lesson.Id}",
                Tag = optionIndex,
                FontSize = 13,
                Foreground = new SolidColorBrush(Color.FromRgb(63, 77, 97)),
                Margin = new Thickness(2, 6, 2, 6),
                Padding = new Thickness(3),
                Cursor = System.Windows.Input.Cursors.Hand
            };
            option.Checked += (_, _) => _selectedQuizAnswer = optionIndex;
            content.Children.Add(option);
        }

        var actions = new StackPanel { Orientation = Orientation.Vertical, Margin = new Thickness(0, 11, 0, 0) };
        var checkButton = new Button
        {
            Content = "Проверить ответ",
            Style = (Style)FindResource("PrimaryButtonStyle")
        };
        checkButton.Click += (_, _) => CheckQuizAnswer(lesson);
        actions.Children.Add(checkButton);
        _quizFeedback = new TextBlock
        {
            FontSize = 12,
            TextWrapping = TextWrapping.Wrap,
            VerticalAlignment = VerticalAlignment.Center,
            Margin = new Thickness(0, 9, 0, 0)
        };
        actions.Children.Add(_quizFeedback);
        content.Children.Add(actions);

        return new Border
        {
            Background = Brushes.White,
            BorderBrush = new SolidColorBrush(Color.FromRgb(230, 235, 243)),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(15),
            Padding = new Thickness(22, 19, 22, 21),
            Margin = new Thickness(0, 0, 0, 19),
            Child = content
        };
    }

    private void CheckQuizAnswer(Lesson lesson)
    {
        if (_quizFeedback is null)
        {
            return;
        }

        if (_selectedQuizAnswer is null)
        {
            _quizFeedback.Text = "Сначала выберите вариант ответа.";
            _quizFeedback.Foreground = new SolidColorBrush(Color.FromRgb(180, 119, 26));
            return;
        }

        bool correct = _selectedQuizAnswer == lesson.Quiz.AnswerIndex;
        _quizFeedback.Text = $"{(correct ? "Верно" : "Не совсем")}. {lesson.Quiz.Explanation}";
        _quizFeedback.Foreground = correct
            ? new SolidColorBrush(Color.FromRgb(41, 126, 87))
            : new SolidColorBrush(Color.FromRgb(166, 79, 67));
    }

    private UIElement CreateLessonFooter(int index)
    {
        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var previous = new Button
        {
            Content = "← Предыдущий",
            Style = (Style)FindResource("SecondaryButtonStyle"),
            IsEnabled = index > 0,
            VerticalAlignment = VerticalAlignment.Center
        };
        previous.Click += (_, _) => RenderLesson(index - 1);
        Grid.SetColumn(previous, 0);
        grid.Children.Add(previous);

        _completionButton = new Button
        {
            VerticalAlignment = VerticalAlignment.Center,
            HorizontalAlignment = HorizontalAlignment.Center
        };
        _completionButton.Click += (_, _) => ToggleLessonCompletion();
        Grid.SetColumn(_completionButton, 1);
        grid.Children.Add(_completionButton);

        var next = new Button
        {
            Content = "Следующий урок →",
            Style = (Style)FindResource("SecondaryButtonStyle"),
            IsEnabled = index < _course.Lessons.Count - 1,
            VerticalAlignment = VerticalAlignment.Center
        };
        next.Click += (_, _) => RenderLesson(index + 1);
        Grid.SetColumn(next, 2);
        grid.Children.Add(next);

        return new Border
        {
            Background = Brushes.White,
            CornerRadius = new CornerRadius(14),
            Padding = new Thickness(14),
            Margin = new Thickness(0, 0, 0, 22),
            Child = grid
        };
    }

    private void ToggleLessonCompletion()
    {
        Lesson lesson = _course.Lessons[_currentLessonIndex];
        if (!_completedLessonIds.Add(lesson.Id))
        {
            _completedLessonIds.Remove(lesson.Id);
        }

        try
        {
            _progressStore.Save(_completedLessonIds);
            UpdateCourseProgress();
            BuildNavigation();
            UpdateCompletionButton();
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            MessageBox.Show(
                $"Не удалось сохранить прогресс на этом компьютере. Проверьте права доступа к папке профиля пользователя.\n\n{exception.Message}",
                "Не удалось сохранить прогресс",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
    }

    private void UpdateCourseProgress()
    {
        int total = _course.Lessons.Count;
        int completed = _course.Lessons.Count(lesson => _completedLessonIds.Contains(lesson.Id));
        int percent = total == 0 ? 0 : (int)Math.Round(completed * 100.0 / total);

        CourseProgress.Value = percent;
        SidebarProgressText.Text = $"{completed} из {total} уроков";
        HeaderProgressText.Text = $"{percent}% пройдено";
    }

    private void UpdateCompletionButton()
    {
        if (_completionButton is null || _course.Lessons.Count == 0)
        {
            return;
        }

        bool completed = _completedLessonIds.Contains(_course.Lessons[_currentLessonIndex].Id);
        _completionButton.Content = completed ? "✓  Урок пройден" : "Отметить урок пройденным";
        _completionButton.Style = (Style)FindResource(completed ? "SecondaryButtonStyle" : "PrimaryButtonStyle");
    }
}
