import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  Mic, 
  Plus, 
  CheckSquare, 
  FileText, 
  Users, 
  Calendar,
  Menu,
  X,
  Play,
  Pause,
  Brain,
  MicOff,
  AlertCircle
} from 'lucide-react'
import { analyzeContent } from './lib/contentTriage.js'
import { VoiceInputManager } from './lib/voiceInput.js'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false)
  const [quickAddText, setQuickAddText] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [voiceError, setVoiceError] = useState(null)
  const [contentAnalysis, setContentAnalysis] = useState(null)
  const [isVoiceSupported, setIsVoiceSupported] = useState(false)
  const voiceManager = useRef(null)
  
  // Modal states for manual entry
  const [isAddTaskModalOpen, setIsAddTaskModalOpen] = useState(false)
  const [isAddStakeholderModalOpen, setIsAddStakeholderModalOpen] = useState(false)
  const [isStakeholderDetailModalOpen, setIsStakeholderDetailModalOpen] = useState(false)
  const [selectedStakeholder, setSelectedStakeholder] = useState(null)
  
  // Form states
  const [taskForm, setTaskForm] = useState({
    title: '',
    dueDate: 'Today',
    priority: 'medium',
    description: ''
  })
  
  const [stakeholderForm, setStakeholderForm] = useState({
    name: '',
    role: '',
    company: '',
    department: '',
    email: '',
    phone: '',
    birthday: '',
    personalNotes: '',
    workStyle: '',
    sentiment: 'neutral',
    influence: 5,
    interest: 5,
    tags: []
  })
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Send project update to Alice', dueDate: 'Today', completed: false, priority: 'high' },
    { id: 2, title: 'Review quarterly budget', dueDate: 'Tomorrow', completed: false, priority: 'medium' },
    { id: 3, title: 'Call team meeting', dueDate: 'Oct 8', completed: false, priority: 'low' }
  ])
  const [notes, setNotes] = useState([
    { id: 1, content: 'Alice is concerned about project timeline', timestamp: '2 hours ago' },
    { id: 2, content: 'New marketing strategy ideas from brainstorm', timestamp: '1 day ago' }
  ])
  const [stakeholders, setStakeholders] = useState([
    { 
      id: 1, 
      name: 'Alice Johnson', 
      role: 'Project Manager', 
      sentiment: 'neutral', 
      influence: 8, 
      interest: 9,
      company: 'TechCorp Inc.',
      department: 'Product Development',
      email: 'alice.johnson@techcorp.com',
      phone: '+1 (555) 123-4567',
      birthday: '1985-03-15',
      personalNotes: 'Has two kids, loves hiking on weekends',
      workStyle: 'Detail-oriented, prefers structured meetings',
      lastContact: '2025-10-05',
      tags: ['key-decision-maker', 'technical']
    },
    { 
      id: 2, 
      name: 'Bob Smith', 
      role: 'Senior Developer', 
      sentiment: 'positive', 
      influence: 6, 
      interest: 7,
      company: 'TechCorp Inc.',
      department: 'Engineering',
      email: 'bob.smith@techcorp.com',
      phone: '+1 (555) 234-5678',
      birthday: '1990-07-22',
      personalNotes: 'Coffee enthusiast, plays guitar',
      workStyle: 'Collaborative, open to new technologies',
      lastContact: '2025-10-04',
      tags: ['technical-expert', 'mentor']
    },
    { 
      id: 3, 
      name: 'Carol Davis', 
      role: 'UX Designer', 
      sentiment: 'positive', 
      influence: 5, 
      interest: 8,
      company: 'DesignStudio LLC',
      department: 'Creative',
      email: 'carol.davis@designstudio.com',
      phone: '+1 (555) 345-6789',
      birthday: '1988-11-10',
      personalNotes: 'Marathon runner, vegetarian',
      workStyle: 'Creative, user-focused approach',
      lastContact: '2025-10-03',
      tags: ['creative', 'user-advocate']
    }
  ])

  // Initialize voice input on component mount
  useEffect(() => {
    voiceManager.current = new VoiceInputManager()
    setIsVoiceSupported(voiceManager.current.isSupported)
    
    return () => {
      if (voiceManager.current && voiceManager.current.isListening) {
        voiceManager.current.stopListening()
      }
    }
  }, [])

  // Analyze content when text changes
  useEffect(() => {
    if (quickAddText.trim()) {
      const analysis = analyzeContent(quickAddText)
      setContentAnalysis(analysis)
    } else {
      setContentAnalysis(null)
    }
  }, [quickAddText])

  const toggleTask = (taskId) => {
    setTasks(tasks.map(task => 
      task.id === taskId ? { ...task, completed: !task.completed } : task
    ))
  }

  const handleQuickAdd = (type) => {
    if (!quickAddText.trim()) return
    
    // Use content analysis to enhance the data
    const analysis = contentAnalysis || analyzeContent(quickAddText)
    
    if (type === 'task' || analysis.type === 'task') {
      const newTask = {
        id: tasks.length + 1,
        title: quickAddText,
        dueDate: analysis.extractedData?.dueDate || 'Today',
        completed: false,
        priority: analysis.extractedData?.priority || 'medium'
      }
      setTasks([...tasks, newTask])
    } else if (analysis.type === 'stakeholder_note' && analysis.extractedData?.stakeholderName) {
      // Check if stakeholder exists, if not create a new one
      const existingStakeholder = stakeholders.find(s => 
        s.name.toLowerCase().includes(analysis.extractedData.stakeholderName.toLowerCase())
      )
      
      if (!existingStakeholder) {
        const newStakeholder = {
          id: stakeholders.length + 1,
          name: analysis.extractedData.stakeholderName,
          role: 'Unknown',
          sentiment: 'neutral',
          influence: 5,
          interest: 5
        }
        setStakeholders([...stakeholders, newStakeholder])
      }
      
      // Add the note
      const newNote = {
        id: notes.length + 1,
        content: quickAddText,
        timestamp: 'Just now',
        stakeholder: analysis.extractedData.stakeholderName
      }
      setNotes([...notes, newNote])
    } else {
      const newNote = {
        id: notes.length + 1,
        content: quickAddText,
        timestamp: 'Just now'
      }
      setNotes([...notes, newNote])
    }
    
    setQuickAddText('')
    setContentAnalysis(null)
    setIsQuickAddOpen(false)
  }

  const startRecording = () => {
    if (!voiceManager.current || !isVoiceSupported) {
      setVoiceError({ message: 'Voice input is not supported in this browser' })
      return
    }

    setVoiceError(null)
    
    const success = voiceManager.current.startListening({
      onStart: () => {
        setIsRecording(true)
      },
      onResult: (result) => {
        if (result.isFinal) {
          setQuickAddText(result.final)
          setIsRecording(false)
        } else {
          // Show interim results
          setQuickAddText(result.interim)
        }
      },
      onError: (error) => {
        setVoiceError(error)
        setIsRecording(false)
      },
      onEnd: () => {
        setIsRecording(false)
      }
    })

    if (!success) {
      setVoiceError({ message: 'Failed to start voice recognition' })
    }
  }

  const stopRecording = () => {
    if (voiceManager.current) {
      voiceManager.current.stopListening()
    }
    setIsRecording(false)
  }

  // Manual task creation
  const handleAddTask = () => {
    if (!taskForm.title.trim()) return
    
    const newTask = {
      id: tasks.length + 1,
      title: taskForm.title,
      dueDate: taskForm.dueDate,
      priority: taskForm.priority,
      completed: false,
      description: taskForm.description
    }
    
    setTasks([...tasks, newTask])
    setTaskForm({ title: '', dueDate: 'Today', priority: 'medium', description: '' })
    setIsAddTaskModalOpen(false)
  }

  // Manual stakeholder creation
  const handleAddStakeholder = () => {
    if (!stakeholderForm.name.trim()) return
    
    const newStakeholder = {
      id: stakeholders.length + 1,
      ...stakeholderForm,
      lastContact: new Date().toISOString().split('T')[0],
      tags: stakeholderForm.tags.filter(tag => tag.trim())
    }
    
    setStakeholders([...stakeholders, newStakeholder])
    setStakeholderForm({
      name: '', role: '', company: '', department: '', email: '', phone: '',
      birthday: '', personalNotes: '', workStyle: '', sentiment: 'neutral',
      influence: 5, interest: 5, tags: []
    })
    setIsAddStakeholderModalOpen(false)
  }

  // Update stakeholder
  const handleUpdateStakeholder = () => {
    if (!selectedStakeholder) return
    
    const updatedStakeholders = stakeholders.map(s => 
      s.id === selectedStakeholder.id 
        ? { ...stakeholderForm, id: selectedStakeholder.id, lastContact: new Date().toISOString().split('T')[0] }
        : s
    )
    
    setStakeholders(updatedStakeholders)
    setIsStakeholderDetailModalOpen(false)
    setSelectedStakeholder(null)
  }

  // Open stakeholder detail modal
  const openStakeholderDetail = (stakeholder) => {
    setSelectedStakeholder(stakeholder)
    setStakeholderForm({ ...stakeholder })
    setIsStakeholderDetailModalOpen(true)
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Quick Add Button */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-6">
          <Button 
            onClick={() => setIsQuickAddOpen(true)}
            className="w-full h-16 text-lg font-semibold bg-blue-600 hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex items-center gap-3">
              <Mic className="w-6 h-6" />
              <span>QUICK ADD</span>
              <Plus className="w-6 h-6" />
            </div>
          </Button>
        </CardContent>
      </Card>

      {/* Upcoming Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckSquare className="w-5 h-5" />
            Upcoming Tasks
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {tasks.slice(0, 3).map(task => (
              <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <Checkbox 
                  checked={task.completed}
                  onCheckedChange={() => toggleTask(task.id)}
                />
                <div className="flex-1">
                  <p className={`font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}>
                    {task.title}
                  </p>
                  <p className="text-sm text-gray-500">{task.dueDate}</p>
                </div>
                <Badge variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}>
                  {task.priority}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Notes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Recent Notes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {notes.slice(0, 2).map(note => (
              <div key={note.id} className="p-3 rounded-lg bg-gray-50">
                <p className="text-sm">{note.content}</p>
                <p className="text-xs text-gray-500 mt-1">{note.timestamp}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Key Stakeholders */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Key Stakeholders
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stakeholders.slice(0, 3).map(stakeholder => (
              <div key={stakeholder.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-sm font-semibold text-blue-600">
                    {stakeholder.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">{stakeholder.name}</p>
                  <p className="text-sm text-gray-500">{stakeholder.role}</p>
                </div>
                <Badge variant={stakeholder.sentiment === 'positive' ? 'default' : stakeholder.sentiment === 'neutral' ? 'secondary' : 'destructive'}>
                  {stakeholder.sentiment}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderTaskPlanner = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Task Planner</CardTitle>
            <Button 
              onClick={() => setIsAddTaskModalOpen(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Task
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
            <div>
              <h3 className="font-semibold mb-3">Today</h3>
              <div className="space-y-2">
                {tasks.filter(task => task.dueDate === 'Today').map(task => (
                  <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg border">
                    <Checkbox 
                      checked={task.completed}
                      onCheckedChange={() => toggleTask(task.id)}
                    />
                    <div className="flex-1">
                      <p className={`font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}>
                        {task.title}
                      </p>
                    </div>
                    <Badge variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}>
                      {task.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold mb-3">Upcoming</h3>
              <div className="space-y-2">
                {tasks.filter(task => task.dueDate !== 'Today').map(task => (
                  <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg border">
                    <Checkbox 
                      checked={task.completed}
                      onCheckedChange={() => toggleTask(task.id)}
                    />
                    <div className="flex-1">
                      <p className={`font-medium ${task.completed ? 'line-through text-gray-500' : ''}`}>
                        {task.title}
                      </p>
                      <p className="text-sm text-gray-500">{task.dueDate}</p>
                    </div>
                    <Badge variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}>
                      {task.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderStakeholderMap = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Stakeholder Map</CardTitle>
            <Button 
              onClick={() => setIsAddStakeholderModalOpen(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Stakeholder
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative w-full h-96 border rounded-lg bg-gray-50">
            {/* Grid lines */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-px bg-gray-300"></div>
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-px h-full bg-gray-300"></div>
            </div>
            
            {/* Axis labels */}
            <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 text-sm font-medium">
              Interest
            </div>
            <div className="absolute left-2 top-1/2 transform -translate-y-1/2 -rotate-90 text-sm font-medium">
              Influence
            </div>
            
            {/* Stakeholder dots */}
            {stakeholders.map(stakeholder => {
              const x = (stakeholder.interest / 10) * 80 + 10 // 10-90% of width
              const y = 90 - (stakeholder.influence / 10) * 80 // Inverted Y axis
              
              return (
                <div
                  key={stakeholder.id}
                  className="absolute w-4 h-4 rounded-full bg-blue-600 cursor-pointer hover:bg-blue-700 transition-colors transform -translate-x-2 -translate-y-2"
                  style={{ left: `${x}%`, top: `${y}%` }}
                  title={`${stakeholder.name} - Influence: ${stakeholder.influence}, Interest: ${stakeholder.interest}`}
                />
              )
            })}
          </div>
          
          {/* Stakeholder list */}
          <div className="space-y-3">
            {stakeholders.map(stakeholder => (
              <div 
                key={stakeholder.id} 
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => openStakeholderDetail(stakeholder)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">
                      {stakeholder.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{stakeholder.name}</p>
                    <p className="text-sm text-gray-500">{stakeholder.role}</p>
                    {stakeholder.company && (
                      <p className="text-xs text-gray-400">{stakeholder.company}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm">Influence: {stakeholder.influence}/10</p>
                  <p className="text-sm">Interest: {stakeholder.interest}/10</p>
                  <Badge variant={stakeholder.sentiment === 'positive' ? 'default' : stakeholder.sentiment === 'negative' ? 'destructive' : 'secondary'}>
                    {stakeholder.sentiment}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">MindFlow</h1>
            <nav className="flex gap-4">
              <Button 
                variant={currentView === 'dashboard' ? 'default' : 'ghost'}
                onClick={() => setCurrentView('dashboard')}
                className="flex items-center gap-2"
              >
                <Menu className="w-4 h-4" />
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
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'tasks' && renderTaskPlanner()}
        {currentView === 'stakeholders' && renderStakeholderMap()}
      </main>

      {/* Quick Add Modal */}
      {isQuickAddOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  Quick Add
                  {contentAnalysis && (
                    <Brain className="w-4 h-4 text-blue-500" />
                  )}
                </CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setIsQuickAddOpen(false)
                    setQuickAddText('')
                    setContentAnalysis(null)
                    setVoiceError(null)
                    if (isRecording) stopRecording()
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Type your thought or task..."
                value={quickAddText}
                onChange={(e) => setQuickAddText(e.target.value)}
                className="min-h-24"
              />
              
              {/* Content Analysis Display */}
              {contentAnalysis && (
                <Alert className="border-blue-200 bg-blue-50">
                  <Brain className="w-4 h-4" />
                  <AlertDescription>
                    <div className="space-y-1">
                      <p className="font-medium">
                        Detected: {contentAnalysis.type.replace('_', ' ')} 
                        <span className="text-sm text-gray-500 ml-2">
                          ({Math.round(contentAnalysis.confidence * 100)}% confidence)
                        </span>
                      </p>
                      {contentAnalysis.extractedData?.dueDate && (
                        <p className="text-sm">Due: {contentAnalysis.extractedData.dueDate}</p>
                      )}
                      {contentAnalysis.extractedData?.priority && (
                        <p className="text-sm">Priority: {contentAnalysis.extractedData.priority}</p>
                      )}
                      {contentAnalysis.extractedData?.stakeholderName && (
                        <p className="text-sm">Stakeholder: {contentAnalysis.extractedData.stakeholderName}</p>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Voice Error Display */}
              {voiceError && (
                <Alert variant="destructive">
                  <AlertCircle className="w-4 h-4" />
                  <AlertDescription>{voiceError.message}</AlertDescription>
                </Alert>
              )}
              
              <div className="flex items-center justify-center">
                <Button
                  variant={isRecording ? "destructive" : "outline"}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={!isVoiceSupported}
                  className="flex items-center gap-2"
                >
                  {isRecording ? (
                    <>
                      <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse" />
                      Stop Recording
                    </>
                  ) : !isVoiceSupported ? (
                    <>
                      <MicOff className="w-4 h-4" />
                      Voice Not Supported
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4" />
                      Voice Input
                    </>
                  )}
                </Button>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleQuickAdd('note')}
                  className="flex-1"
                  variant={contentAnalysis?.type === 'task' ? 'outline' : 'default'}
                  disabled={!quickAddText.trim()}
                >
                  Save as Note
                </Button>
                <Button 
                  onClick={() => handleQuickAdd('task')}
                  className="flex-1"
                  variant={contentAnalysis?.type === 'task' ? 'default' : 'outline'}
                  disabled={!quickAddText.trim()}
                >
                  Save as Task
                </Button>
              </div>
              
              {contentAnalysis?.suggestions && contentAnalysis.suggestions.length > 0 && (
                <div className="text-xs text-gray-500 text-center">
                  {contentAnalysis.suggestions[0]}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Task Modal */}
      {isAddTaskModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Add New Task</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setIsAddTaskModalOpen(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Task Title</label>
                <Input
                  placeholder="Enter task title..."
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({...taskForm, title: e.target.value})}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Description (Optional)</label>
                <Textarea
                  placeholder="Add task description..."
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
                  className="min-h-20"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Due Date</label>
                  <select 
                    className="w-full p-2 border rounded-md"
                    value={taskForm.dueDate}
                    onChange={(e) => setTaskForm({...taskForm, dueDate: e.target.value})}
                  >
                    <option value="Today">Today</option>
                    <option value="Tomorrow">Tomorrow</option>
                    <option value="This Week">This Week</option>
                    <option value="Next Week">Next Week</option>
                    <option value="Oct 8">Oct 8</option>
                    <option value="Oct 15">Oct 15</option>
                  </select>
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Priority</label>
                  <select 
                    className="w-full p-2 border rounded-md"
                    value={taskForm.priority}
                    onChange={(e) => setTaskForm({...taskForm, priority: e.target.value})}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => setIsAddTaskModalOpen(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAddTask}
                  className="flex-1"
                  disabled={!taskForm.title.trim()}
                >
                  Add Task
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Stakeholder Modal */}
      {isAddStakeholderModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Add New Stakeholder</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setIsAddStakeholderModalOpen(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Full Name *</label>
                    <Input
                      placeholder="John Doe"
                      value={stakeholderForm.name}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Role/Title</label>
                    <Input
                      placeholder="Project Manager"
                      value={stakeholderForm.role}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, role: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Professional Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Professional Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Company</label>
                    <Input
                      placeholder="TechCorp Inc."
                      value={stakeholderForm.company}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, company: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Department</label>
                    <Input
                      placeholder="Engineering"
                      value={stakeholderForm.department}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, department: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Work Style</label>
                  <Textarea
                    placeholder="Collaborative, detail-oriented, prefers structured meetings..."
                    value={stakeholderForm.workStyle}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, workStyle: e.target.value})}
                    className="min-h-20"
                  />
                </div>
              </div>

              {/* Contact Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Contact Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Email</label>
                    <Input
                      type="email"
                      placeholder="john.doe@company.com"
                      value={stakeholderForm.email}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, email: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Phone</label>
                    <Input
                      placeholder="+1 (555) 123-4567"
                      value={stakeholderForm.phone}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, phone: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Personal Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Personal Information</h3>
                <div>
                  <label className="text-sm font-medium mb-2 block">Birthday</label>
                  <Input
                    type="date"
                    value={stakeholderForm.birthday}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, birthday: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Personal Notes</label>
                  <Textarea
                    placeholder="Has two kids, loves hiking, coffee enthusiast..."
                    value={stakeholderForm.personalNotes}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, personalNotes: e.target.value})}
                    className="min-h-20"
                  />
                </div>
              </div>

              {/* Relationship Mapping */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Relationship Mapping</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Sentiment</label>
                    <select 
                      className="w-full p-2 border rounded-md"
                      value={stakeholderForm.sentiment}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, sentiment: e.target.value})}
                    >
                      <option value="positive">Positive</option>
                      <option value="neutral">Neutral</option>
                      <option value="negative">Negative</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Influence (1-10)</label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={stakeholderForm.influence}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, influence: parseInt(e.target.value) || 5})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Interest (1-10)</label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={stakeholderForm.interest}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, interest: parseInt(e.target.value) || 5})}
                    />
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Tags</h3>
                <Input
                  placeholder="Enter tags separated by commas (e.g., decision-maker, technical, mentor)"
                  value={stakeholderForm.tags.join(', ')}
                  onChange={(e) => setStakeholderForm({
                    ...stakeholderForm, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                  })}
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => setIsAddStakeholderModalOpen(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAddStakeholder}
                  className="flex-1"
                  disabled={!stakeholderForm.name.trim()}
                >
                  Add Stakeholder
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stakeholder Detail Modal */}
      {isStakeholderDetailModalOpen && selectedStakeholder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Edit Stakeholder: {selectedStakeholder.name}</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setIsStakeholderDetailModalOpen(false)
                    setSelectedStakeholder(null)
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Full Name *</label>
                    <Input
                      placeholder="John Doe"
                      value={stakeholderForm.name}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Role/Title</label>
                    <Input
                      placeholder="Project Manager"
                      value={stakeholderForm.role}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, role: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Professional Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Professional Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Company</label>
                    <Input
                      placeholder="TechCorp Inc."
                      value={stakeholderForm.company}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, company: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Department</label>
                    <Input
                      placeholder="Engineering"
                      value={stakeholderForm.department}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, department: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Work Style</label>
                  <Textarea
                    placeholder="Collaborative, detail-oriented, prefers structured meetings..."
                    value={stakeholderForm.workStyle}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, workStyle: e.target.value})}
                    className="min-h-20"
                  />
                </div>
              </div>

              {/* Contact Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Contact Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Email</label>
                    <Input
                      type="email"
                      placeholder="john.doe@company.com"
                      value={stakeholderForm.email}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, email: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Phone</label>
                    <Input
                      placeholder="+1 (555) 123-4567"
                      value={stakeholderForm.phone}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, phone: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Personal Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Personal Information</h3>
                <div>
                  <label className="text-sm font-medium mb-2 block">Birthday</label>
                  <Input
                    type="date"
                    value={stakeholderForm.birthday}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, birthday: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Personal Notes</label>
                  <Textarea
                    placeholder="Has two kids, loves hiking, coffee enthusiast..."
                    value={stakeholderForm.personalNotes}
                    onChange={(e) => setStakeholderForm({...stakeholderForm, personalNotes: e.target.value})}
                    className="min-h-20"
                  />
                </div>
              </div>

              {/* Relationship Mapping */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Relationship Mapping</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Sentiment</label>
                    <select 
                      className="w-full p-2 border rounded-md"
                      value={stakeholderForm.sentiment}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, sentiment: e.target.value})}
                    >
                      <option value="positive">Positive</option>
                      <option value="neutral">Neutral</option>
                      <option value="negative">Negative</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Influence (1-10)</label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={stakeholderForm.influence}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, influence: parseInt(e.target.value) || 5})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Interest (1-10)</label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={stakeholderForm.interest}
                      onChange={(e) => setStakeholderForm({...stakeholderForm, interest: parseInt(e.target.value) || 5})}
                    />
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Tags</h3>
                <Input
                  placeholder="Enter tags separated by commas (e.g., decision-maker, technical, mentor)"
                  value={stakeholderForm.tags.join(', ')}
                  onChange={(e) => setStakeholderForm({
                    ...stakeholderForm, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                  })}
                />
                {stakeholderForm.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {stakeholderForm.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary">{tag}</Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Last Contact */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Contact History</h3>
                <p className="text-sm text-gray-600">
                  Last contact: {selectedStakeholder.lastContact ? new Date(selectedStakeholder.lastContact).toLocaleDateString() : 'Never'}
                </p>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setIsStakeholderDetailModalOpen(false)
                    setSelectedStakeholder(null)
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleUpdateStakeholder}
                  className="flex-1"
                  disabled={!stakeholderForm.name.trim()}
                >
                  Update Stakeholder
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default App
