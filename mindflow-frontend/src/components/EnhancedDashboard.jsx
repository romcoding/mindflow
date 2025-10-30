import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth.jsx';
import { tasksAPI, stakeholdersAPI, notesAPI } from '../lib/api.js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

// Import our new components
import StakeholderNetworkMap from './StakeholderNetworkMap.jsx';
import StakeholderDetailModal from './StakeholderDetailModal.jsx';
import KanbanBoard from './KanbanBoard.jsx';
import TaskCalendar from './TaskCalendar.jsx';
import UserProfile from './UserProfile.jsx';

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
  User,
  Calendar,
  Network,
  BarChart3,
  Target,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Brain,
  Zap,
  Eye,
  Edit,
  Trash2,
  Filter,
  Search,
  Bell,
  Menu,
  X
} from 'lucide-react';

const EnhancedDashboard = () => {
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');
  const [tasks, setTasks] = useState([]);
  const [stakeholders, setStakeholders] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false);
  const [isStakeholderModalOpen, setIsStakeholderModalOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [selectedStakeholder, setSelectedStakeholder] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Quick Add state
  const [quickAddText, setQuickAddText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // Task view state
  const [taskView, setTaskView] = useState('kanban'); // 'kanban' or 'calendar'

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
      
      // Load relationships if available
      try {
        const relationshipsRes = await fetch('/api/stakeholder-relationships');
        if (relationshipsRes.ok) {
          const relData = await relationshipsRes.json();
          setRelationships(relData.relationships || []);
        }
      } catch (error) {
        console.log('Relationships not available yet');
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced content analysis with AI-like intelligence
  const analyzeContent = (text) => {
    const lowerText = text.toLowerCase();
    
    // Task indicators with more sophisticated patterns
    const taskPatterns = [
      /\b(task|todo|remind|schedule|meeting|call|email|deadline|due|complete|finish|work on)\b/i,
      /\b(need to|have to|must|should|will|going to)\b/i,
      /\b(by|before|until|on|at)\s+\d/i // Date patterns
    ];
    
    // Stakeholder indicators
    const stakeholderPatterns = [
      /\b(person|contact|colleague|client|manager|team|boss|employee|partner)\b/i,
      /\b(meet with|talk to|call|email|discuss with)\s+([A-Z][a-z]+)/i,
      /\b([A-Z][a-z]+)\s+(said|mentioned|thinks|wants|needs)\b/i
    ];
    
    // Note indicators
    const notePatterns = [
      /\b(idea|thought|remember|note|insight|observation)\b/i,
      /\b(interesting|important|key point|takeaway)\b/i
    ];

    const isTask = taskPatterns.some(pattern => pattern.test(text));
    const isStakeholder = stakeholderPatterns.some(pattern => pattern.test(text));
    const isNote = notePatterns.some(pattern => pattern.test(text)) || (!isTask && !isStakeholder);
    
    // Priority detection
    const urgentKeywords = ['urgent', 'asap', 'critical', 'emergency', 'immediately'];
    const highKeywords = ['important', 'high priority', 'deadline', 'soon'];
    const mediumKeywords = ['medium', 'normal', 'regular'];
    
    let priority = 'low';
    if (urgentKeywords.some(keyword => lowerText.includes(keyword))) {
      priority = 'urgent';
    } else if (highKeywords.some(keyword => lowerText.includes(keyword))) {
      priority = 'high';
    } else if (mediumKeywords.some(keyword => lowerText.includes(keyword))) {
      priority = 'medium';
    }
    
    // Due date detection with more patterns
    const dueDatePatterns = {
      'today': /\b(today|now|immediately)\b/i,
      'tomorrow': /\b(tomorrow|next day)\b/i,
      'this week': /\b(this week|by friday|end of week)\b/i,
      'next week': /\b(next week|following week)\b/i,
      'this month': /\b(this month|end of month)\b/i
    };
    
    let dueDate = null;
    for (const [date, pattern] of Object.entries(dueDatePatterns)) {
      if (pattern.test(text)) {
        dueDate = date;
        break;
      }
    }

    // Extract names for stakeholders
    const nameMatches = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g);
    const extractedNames = nameMatches ? nameMatches.filter(name => 
      !['I', 'The', 'This', 'That', 'Today', 'Tomorrow'].includes(name)
    ) : [];

    return {
      type: isTask ? 'task' : isStakeholder ? 'stakeholder' : 'note',
      priority,
      dueDate,
      extractedNames,
      confidence: isTask ? 0.9 : isStakeholder ? 0.8 : 0.7,
      suggestions: {
        task: isTask ? text : `Create task: ${text.substring(0, 50)}...`,
        stakeholder: extractedNames.length > 0 ? `Add contact: ${extractedNames[0]}` : null,
        note: `Save as note: ${text.substring(0, 50)}...`
      }
    };
  };

  const handleQuickAdd = async (type = null) => {
    if (!quickAddText.trim()) return;

    const analysis = type ? { ...analysisResult, type } : analyzeContent(quickAddText);
    
    try {
      if (analysis.type === 'task') {
        await tasksAPI.createTask({
          title: quickAddText,
          description: '',
          priority: analysis.priority,
          due_date: analysis.dueDate,
          status: 'todo',
          board_column: 'todo'
        });
      } else if (analysis.type === 'stakeholder') {
        const name = analysis.extractedNames[0] || 'New Contact';
        await stakeholdersAPI.createStakeholder({
          name: name,
          personal_notes: quickAddText,
          sentiment: 'neutral',
          influence: 5,
          interest: 5
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
      loadData();
    } catch (error) {
      console.error('Failed to create item:', error);
    }
  };

  // Handle voice input
  const startVoiceRecording = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuickAddText(transcript);
        setAnalysisResult(analyzeContent(transcript));
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
    } else {
      alert('Speech recognition not supported in this browser');
    }
  };

  // Task management functions
  const handleTaskMove = async (taskId, newColumn, newPosition) => {
    try {
      await tasksAPI.updateTask(taskId, {
        board_column: newColumn,
        board_position: newPosition
      });
      loadData();
    } catch (error) {
      console.error('Failed to move task:', error);
    }
  };

  const handleTaskClick = (task) => {
    // Open task detail modal (to be implemented)
    console.log('Task clicked:', task);
  };

  // Stakeholder management functions
  const handleStakeholderClick = (stakeholder) => {
    setSelectedStakeholder(stakeholder);
    setIsStakeholderModalOpen(true);
  };

  const handleStakeholderSave = async (stakeholderData) => {
    try {
      if (selectedStakeholder) {
        await stakeholdersAPI.updateStakeholder(selectedStakeholder.id, stakeholderData);
      } else {
        await stakeholdersAPI.createStakeholder(stakeholderData);
      }
      setIsStakeholderModalOpen(false);
      setSelectedStakeholder(null);
      loadData();
    } catch (error) {
      console.error('Failed to save stakeholder:', error);
    }
  };

  // Get dashboard stats
  const getDashboardStats = () => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === 'done').length;
    const overdueTasks = tasks.filter(t => {
      if (!t.due_date) return false;
      return new Date(t.due_date) < new Date() && t.status !== 'done';
    }).length;
    
    const totalStakeholders = stakeholders.length;
    const positiveStakeholders = stakeholders.filter(s => s.sentiment === 'positive').length;
    const highInfluenceStakeholders = stakeholders.filter(s => s.influence >= 8).length;

    return {
      totalTasks,
      completedTasks,
      overdueTasks,
      totalStakeholders,
      positiveStakeholders,
      highInfluenceStakeholders,
      totalNotes: notes.length,
      completionRate: totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
    };
  };

  const stats = getDashboardStats();

  // Navigation items
  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'tasks', label: 'Tasks', icon: CheckSquare },
    { id: 'stakeholders', label: 'Stakeholders', icon: Users },
    { id: 'notes', label: 'Notes', icon: StickyNote },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 }
  ];

  // Render different views
  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Welcome back, {user?.name}!</h2>
            <p className="text-blue-100">Here's what's happening with your productivity today.</p>
          </div>
          <div className="hidden md:block">
            <Brain className="h-16 w-16 text-blue-200" />
          </div>
        </div>
      </div>

      {/* Quick Add Section */}
      <Card>
        <CardContent className="p-6">
          <Button 
            onClick={() => setIsQuickAddOpen(true)}
            className="w-full h-16 text-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            <Mic className="w-6 h-6 mr-2" />
            QUICK ADD - Capture your thoughts instantly
            <Plus className="w-6 h-6 ml-2" />
          </Button>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Active Tasks</p>
                <p className="text-2xl font-bold text-blue-600">{stats.totalTasks - stats.completedTasks}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-2xl font-bold text-green-600">{stats.completedTasks}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-600" />
              <div>
                <p className="text-sm font-medium">Stakeholders</p>
                <p className="text-2xl font-bold text-purple-600">{stats.totalStakeholders}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-orange-600" />
              <div>
                <p className="text-sm font-medium">Completion Rate</p>
                <p className="text-2xl font-bold text-orange-600">{stats.completionRate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Tasks */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming Tasks</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setCurrentView('tasks')}>
              View All
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {tasks.filter(t => t.status !== 'done').slice(0, 5).map(task => (
              <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer">
                <div className={`w-3 h-3 rounded-full ${
                  task.priority === 'urgent' ? 'bg-red-500' :
                  task.priority === 'high' ? 'bg-orange-500' :
                  task.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                }`} />
                <div className="flex-1">
                  <p className="font-medium">{task.title}</p>
                  <p className="text-sm text-gray-600">{task.due_date || 'No due date'}</p>
                </div>
                <Badge variant={task.priority === 'urgent' ? 'destructive' : 'outline'}>
                  {task.priority}
                </Badge>
              </div>
            ))}
            {tasks.filter(t => t.status !== 'done').length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>All caught up! No pending tasks.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Key Stakeholders */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Key Stakeholders</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setCurrentView('stakeholders')}>
              View Network
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {stakeholders.slice(0, 5).map(stakeholder => (
              <div 
                key={stakeholder.id} 
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer"
                onClick={() => handleStakeholderClick(stakeholder)}
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {stakeholder.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <p className="font-medium">{stakeholder.name}</p>
                  <p className="text-sm text-gray-600">{stakeholder.role || 'No role specified'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-gray-500">
                    Influence: {stakeholder.influence || 5}/10
                  </div>
                  <Badge variant={
                    stakeholder.sentiment === 'positive' ? 'default' : 
                    stakeholder.sentiment === 'negative' ? 'destructive' : 'secondary'
                  }>
                    {stakeholder.sentiment || 'neutral'}
                  </Badge>
                </div>
              </div>
            ))}
            {stakeholders.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No stakeholders yet. Add your first contact!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Quick Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">Productivity Trend</h4>
              <p className="text-sm text-blue-700 mt-1">
                You've completed {stats.completedTasks} tasks this week. Keep it up!
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-900">Network Health</h4>
              <p className="text-sm text-purple-700 mt-1">
                {stats.positiveStakeholders} positive relationships out of {stats.totalStakeholders} contacts.
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <h4 className="font-medium text-orange-900">Focus Areas</h4>
              <p className="text-sm text-orange-700 mt-1">
                {stats.overdueTasks > 0 ? `${stats.overdueTasks} overdue tasks need attention.` : 'All tasks are on track!'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderTasks = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Task Management</h2>
        <div className="flex items-center gap-2">
          <Button
            variant={taskView === 'kanban' ? 'default' : 'outline'}
            onClick={() => setTaskView('kanban')}
            size="sm"
          >
            Kanban
          </Button>
          <Button
            variant={taskView === 'calendar' ? 'default' : 'outline'}
            onClick={() => setTaskView('calendar')}
            size="sm"
          >
            <Calendar className="h-4 w-4 mr-1" />
            Calendar
          </Button>
        </div>
      </div>

      {taskView === 'kanban' ? (
        <KanbanBoard
          tasks={tasks}
          stakeholders={stakeholders}
          onTaskMove={handleTaskMove}
          onTaskClick={handleTaskClick}
          onAddTask={(column) => {
            // Open task creation modal for specific column
            setIsQuickAddOpen(true);
          }}
        />
      ) : (
        <TaskCalendar
          tasks={tasks}
          stakeholders={stakeholders}
          onTaskClick={handleTaskClick}
          onDateSelect={(slotInfo) => {
            // Open task creation for selected date
            setIsQuickAddOpen(true);
          }}
        />
      )}
    </div>
  );

  const renderStakeholders = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Stakeholder Network</h2>
        <Button onClick={() => {
          setSelectedStakeholder(null);
          setIsStakeholderModalOpen(true);
        }}>
          <Plus className="h-4 w-4 mr-2" />
          Add Stakeholder
        </Button>
      </div>

      <StakeholderNetworkMap
        stakeholders={stakeholders}
        relationships={relationships}
        onNodeClick={handleStakeholderClick}
      />
    </div>
  );

  const renderNotes = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Notes & Ideas</h2>
        <Button onClick={() => setIsQuickAddOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Note
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {notes.map(note => (
          <Card key={note.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4">
              <p className="text-sm text-gray-600 mb-2">
                {new Date(note.created_at).toLocaleDateString()}
              </p>
              <p className="text-gray-900">{note.content}</p>
              {note.category && (
                <Badge variant="outline" className="mt-2">
                  {note.category}
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
        {notes.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            <StickyNote className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">No notes yet</p>
            <p>Start capturing your thoughts and ideas!</p>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg font-medium">Loading your workspace...</p>
          <p className="text-gray-600">Organizing your productivity data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MindFlow</h1>
                <p className="text-sm text-gray-600 hidden md:block">Your Personal Productivity Hub</p>
              </div>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-2">
              {navigationItems.map(item => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={currentView === item.id ? 'default' : 'ghost'}
                    onClick={() => setCurrentView(item.id)}
                    className="flex items-center gap-2"
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Button>
                );
              })}
            </nav>

            {/* User Menu */}
            <div className="flex items-center gap-2">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <Bell className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Notifications</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setIsProfileOpen(true)}
                    >
                      <User className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Profile & Settings</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>

              {/* Mobile menu button */}
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden"
                onClick={() => setIsMobileMenuOpen(true)}
              >
                <Menu className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setIsMobileMenuOpen(false)} />
          <div className="fixed right-0 top-0 h-full w-64 bg-white shadow-xl">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Navigation</h2>
                <Button variant="ghost" size="sm" onClick={() => setIsMobileMenuOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <nav className="p-4 space-y-2">
              {navigationItems.map(item => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={currentView === item.id ? 'default' : 'ghost'}
                    onClick={() => {
                      setCurrentView(item.id);
                      setIsMobileMenuOpen(false);
                    }}
                    className="w-full justify-start gap-2"
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Button>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'tasks' && renderTasks()}
        {currentView === 'stakeholders' && renderStakeholders()}
        {currentView === 'notes' && renderNotes()}
        {currentView === 'analytics' && (
          <div className="text-center py-12">
            <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
            <p className="text-gray-600">Advanced insights and productivity analytics will be available here.</p>
          </div>
        )}
      </main>

      {/* Quick Add Modal */}
      <Dialog open={isQuickAddOpen} onOpenChange={setIsQuickAddOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Quick Add - Capture Your Thoughts
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="What's on your mind? Speak or type your thoughts..."
                value={quickAddText}
                onChange={(e) => {
                  setQuickAddText(e.target.value);
                  if (e.target.value) {
                    setAnalysisResult(analyzeContent(e.target.value));
                  } else {
                    setAnalysisResult(null);
                  }
                }}
                className="flex-1 min-h-[100px]"
              />
              <Button
                variant={isRecording ? "destructive" : "outline"}
                onClick={startVoiceRecording}
                className="self-start"
              >
                {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
            </div>

            {analysisResult && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="p-4">
                  <h4 className="font-medium text-blue-900 mb-2">AI Analysis</h4>
                  <div className="space-y-2">
                    <p className="text-sm text-blue-800">
                      Detected as: <Badge variant="outline">{analysisResult.type}</Badge>
                      {analysisResult.priority && (
                        <>
                          {' '}• Priority: <Badge variant="outline">{analysisResult.priority}</Badge>
                        </>
                      )}
                      {analysisResult.dueDate && (
                        <>
                          {' '}• Due: <Badge variant="outline">{analysisResult.dueDate}</Badge>
                        </>
                      )}
                    </p>
                    <p className="text-xs text-blue-600">
                      Confidence: {Math.round(analysisResult.confidence * 100)}%
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsQuickAddOpen(false)}>
                Cancel
              </Button>
              {analysisResult && (
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => handleQuickAdd('task')}>
                    Save as Task
                  </Button>
                  <Button variant="outline" onClick={() => handleQuickAdd('stakeholder')}>
                    Save as Contact
                  </Button>
                  <Button variant="outline" onClick={() => handleQuickAdd('note')}>
                    Save as Note
                  </Button>
                </div>
              )}
              <Button onClick={() => handleQuickAdd()}>
                Smart Add
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Stakeholder Detail Modal */}
      <StakeholderDetailModal
        isOpen={isStakeholderModalOpen}
        onClose={() => {
          setIsStakeholderModalOpen(false);
          setSelectedStakeholder(null);
        }}
        stakeholder={selectedStakeholder}
        onSave={handleStakeholderSave}
        isEditing={true}
      />

      {/* User Profile Modal */}
      <Dialog open={isProfileOpen} onOpenChange={setIsProfileOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden p-0">
          <UserProfile
            user={user}
            onUpdateProfile={(profileData) => {
              // Handle profile update
              console.log('Update profile:', profileData);
            }}
            onChangePassword={(passwordData) => {
              // Handle password change
              console.log('Change password:', passwordData);
            }}
            onDeleteAccount={() => {
              // Handle account deletion
              console.log('Delete account');
            }}
            onLogout={logout}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EnhancedDashboard;
