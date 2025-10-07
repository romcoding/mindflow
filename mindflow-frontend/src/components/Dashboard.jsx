import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { tasksAPI, stakeholdersAPI, notesAPI } from '../lib/api.js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { 
  LayoutDashboard, 
  CheckSquare, 
  Users, 
  StickyNote, 
  Plus, 
  Mic, 
  MicOff,
  LogOut,
  Settings,
  User
} from 'lucide-react';

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');
  const [tasks, setTasks] = useState([]);
  const [stakeholders, setStakeholders] = useState([]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Quick Add Modal State
  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false);
  const [quickAddText, setQuickAddText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tasksRes, stakeholdersRes, notesRes] = await Promise.all([
        tasksAPI.getTasks(),
        stakeholdersAPI.getStakeholders(),
        notesAPI.getNotes()
      ]);
      
      setTasks(tasksRes.data.tasks || []);
      setStakeholders(stakeholdersRes.data.stakeholders || []);
      setNotes(notesRes.data.notes || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeContent = (text) => {
    // Simple content analysis (can be enhanced with AI)
    const lowerText = text.toLowerCase();
    
    // Task indicators
    const taskKeywords = ['task', 'todo', 'remind', 'schedule', 'meeting', 'call', 'email', 'deadline'];
    const isTask = taskKeywords.some(keyword => lowerText.includes(keyword));
    
    // Stakeholder indicators
    const stakeholderKeywords = ['person', 'contact', 'colleague', 'client', 'manager', 'team'];
    const isStakeholder = stakeholderKeywords.some(keyword => lowerText.includes(keyword));
    
    // Priority detection
    const highPriorityKeywords = ['urgent', 'asap', 'important', 'critical', 'deadline'];
    const priority = highPriorityKeywords.some(keyword => lowerText.includes(keyword)) ? 'high' : 'medium';
    
    // Due date detection
    const dueDateKeywords = {
      'today': 'Today',
      'tomorrow': 'Tomorrow',
      'next week': 'Next Week',
      'this week': 'This Week'
    };
    
    let dueDate = 'Today';
    for (const [keyword, date] of Object.entries(dueDateKeywords)) {
      if (lowerText.includes(keyword)) {
        dueDate = date;
        break;
      }
    }

    return {
      type: isTask ? 'task' : isStakeholder ? 'stakeholder' : 'note',
      priority,
      dueDate,
      confidence: 0.8
    };
  };

  const handleQuickAdd = async () => {
    if (!quickAddText.trim()) return;

    const analysis = analyzeContent(quickAddText);
    
    try {
      if (analysis.type === 'task') {
        await tasksAPI.createTask({
          title: quickAddText,
          priority: analysis.priority,
          due_date: analysis.dueDate
        });
      } else if (analysis.type === 'stakeholder') {
        // Extract name from text (simple approach)
        const words = quickAddText.split(' ');
        const name = words.find(word => word.charAt(0) === word.charAt(0).toUpperCase()) || 'New Contact';
        
        await stakeholdersAPI.createStakeholder({
          name: name,
          personal_notes: quickAddText
        });
      } else {
        await notesAPI.createNote({
          content: quickAddText,
          category: 'general'
        });
      }
      
      setQuickAddText('');
      setIsQuickAddOpen(false);
      setAnalysisResult(null);
      loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to create item:', error);
    }
  };

  const toggleTask = async (taskId) => {
    try {
      await tasksAPI.toggleTask(taskId);
      loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to toggle task:', error);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Quick Add Section */}
      <Card>
        <CardContent className="p-6">
          <Button 
            onClick={() => setIsQuickAddOpen(true)}
            className="w-full h-16 text-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            <Mic className="w-6 h-6 mr-2" />
            QUICK ADD
            <Plus className="w-6 h-6 ml-2" />
          </Button>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <CheckSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.filter(t => !t.completed).length}</div>
            <p className="text-xs text-muted-foreground">
              {tasks.filter(t => t.completed).length} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stakeholders</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stakeholders.length}</div>
            <p className="text-xs text-muted-foreground">
              {stakeholders.filter(s => s.sentiment === 'positive').length} positive relationships
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Notes</CardTitle>
            <StickyNote className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{notes.length}</div>
            <p className="text-xs text-muted-foreground">
              Recent thoughts and ideas
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Tasks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tasks.filter(t => !t.completed).slice(0, 5).map(task => (
              <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg border">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => toggleTask(task.id)}
                  className="rounded"
                />
                <div className="flex-1">
                  <p className="font-medium">{task.title}</p>
                  <p className="text-sm text-muted-foreground">{task.due_date}</p>
                </div>
                <Badge variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}>
                  {task.priority}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Key Stakeholders</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {stakeholders.slice(0, 5).map(stakeholder => (
              <div key={stakeholder.id} className="flex items-center gap-3 p-3 rounded-lg border">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">
                    {stakeholder.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">{stakeholder.name}</p>
                  <p className="text-sm text-muted-foreground">{stakeholder.role}</p>
                </div>
                <Badge variant={stakeholder.sentiment === 'positive' ? 'default' : stakeholder.sentiment === 'negative' ? 'destructive' : 'secondary'}>
                  {stakeholder.sentiment}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p>Loading your workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">M</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">MindFlow</h1>
            </div>
            
            <nav className="flex items-center gap-4">
              <Button 
                variant={currentView === 'dashboard' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('dashboard')}
                className="flex items-center gap-2"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Button>
              <Button 
                variant={currentView === 'tasks' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('tasks')}
                className="flex items-center gap-2"
              >
                <CheckSquare className="w-4 h-4" />
                Tasks
              </Button>
              <Button 
                variant={currentView === 'stakeholders' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('stakeholders')}
                className="flex items-center gap-2"
              >
                <Users className="w-4 h-4" />
                Stakeholders
              </Button>
              
              <div className="flex items-center gap-2 ml-4 pl-4 border-l">
                <span className="text-sm text-muted-foreground">
                  Welcome, {user?.first_name || user?.username}
                </span>
                <Button variant="ghost" size="sm">
                  <Settings className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={logout}>
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'tasks' && <div>Tasks view - Coming soon</div>}
        {currentView === 'stakeholders' && <div>Stakeholders view - Coming soon</div>}
      </main>

      {/* Quick Add Modal */}
      {isQuickAddOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Quick Add</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="What's on your mind? Speak or type..."
                value={quickAddText}
                onChange={(e) => {
                  setQuickAddText(e.target.value);
                  if (e.target.value) {
                    setAnalysisResult(analyzeContent(e.target.value));
                  } else {
                    setAnalysisResult(null);
                  }
                }}
                className="min-h-24"
              />
              
              {analysisResult && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium">AI Analysis:</p>
                  <p className="text-sm text-muted-foreground">
                    Detected as: <Badge variant="outline">{analysisResult.type}</Badge>
                    {analysisResult.type === 'task' && (
                      <>
                        {' '}Priority: <Badge variant="outline">{analysisResult.priority}</Badge>
                        {' '}Due: <Badge variant="outline">{analysisResult.dueDate}</Badge>
                      </>
                    )}
                  </p>
                </div>
              )}
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setIsQuickAddOpen(false);
                    setQuickAddText('');
                    setAnalysisResult(null);
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleQuickAdd}
                  disabled={!quickAddText.trim()}
                  className="flex-1"
                >
                  Add {analysisResult?.type || 'Item'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
