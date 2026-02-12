import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';
import { 
  Plus, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  Circle, 
  User,
  MoreHorizontal,
  Filter,
  SortAsc,
  Eye,
  Edit,
  Trash2,
  Flag,
  Zap,
  Target
} from 'lucide-react';
import { format, isAfter, isBefore, addDays } from 'date-fns';

const KanbanBoard = ({ 
  tasks = [], 
  onTaskMove, 
  onTaskClick, 
  onTaskEdit, 
  onTaskDelete, 
  onAddTask,
  stakeholders = [],
  className = "" 
}) => {
  const [columns, setColumns] = useState({
    todo: {
      id: 'todo',
      title: 'To Do',
      color: 'bg-gray-100',
      tasks: []
    },
    in_progress: {
      id: 'in_progress',
      title: 'In Progress',
      color: 'bg-blue-100',
      tasks: []
    },
    review: {
      id: 'review',
      title: 'Review',
      color: 'bg-yellow-100',
      tasks: []
    },
    done: {
      id: 'done',
      title: 'Done',
      color: 'bg-green-100',
      tasks: []
    }
  });

  const [filters, setFilters] = useState({
    priority: 'all',
    assignee: 'all',
    dueDate: 'all'
  });

  // Organize tasks by column
  useEffect(() => {
    const organizedColumns = { ...columns };
    
    // Reset tasks in columns
    Object.keys(organizedColumns).forEach(columnId => {
      organizedColumns[columnId].tasks = [];
    });

    // Filter and sort tasks
    const filteredTasks = tasks.filter(task => {
      if (filters.priority !== 'all' && task.priority !== filters.priority) return false;
      if (filters.assignee !== 'all' && task.assigned_stakeholder_id !== parseInt(filters.assignee)) return false;
      if (filters.dueDate !== 'all') {
        const today = new Date();
        const taskDueDate = task.due_date ? new Date(task.due_date) : null;
        
        switch (filters.dueDate) {
          case 'overdue':
            if (!taskDueDate || !isBefore(taskDueDate, today)) return false;
            break;
          case 'today':
            if (!taskDueDate || format(taskDueDate, 'yyyy-MM-dd') !== format(today, 'yyyy-MM-dd')) return false;
            break;
          case 'week':
            if (!taskDueDate || isAfter(taskDueDate, addDays(today, 7))) return false;
            break;
        }
      }
      return true;
    });

    // Add tasks to appropriate columns
    filteredTasks.forEach(task => {
      const columnId = task.board_column || 'todo';
      if (organizedColumns[columnId]) {
        organizedColumns[columnId].tasks.push(task);
      }
    });

    // Sort tasks within each column by board_position
    Object.keys(organizedColumns).forEach(columnId => {
      organizedColumns[columnId].tasks.sort((a, b) => (a.board_position || 0) - (b.board_position || 0));
    });

    setColumns(organizedColumns);
  }, [tasks, filters]);

  const handleDragEnd = (result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;

    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }

    const taskId = parseInt(draggableId);
    const newColumn = destination.droppableId;
    const newPosition = destination.index;

    if (onTaskMove) {
      onTaskMove(taskId, newColumn, newPosition);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      urgent: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-white',
      low: 'bg-green-500 text-white'
    };
    return colors[priority] || colors.medium;
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent':
        return <AlertTriangle className="h-3 w-3" />;
      case 'high':
        return <Flag className="h-3 w-3" />;
      case 'medium':
        return <Circle className="h-3 w-3" />;
      case 'low':
        return <Circle className="h-3 w-3" />;
      default:
        return <Circle className="h-3 w-3" />;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'in_progress':
        return <Zap className="h-4 w-4 text-blue-600" />;
      case 'waiting':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    return isBefore(new Date(dueDate), new Date());
  };

  const getDueDateColor = (dueDate) => {
    if (!dueDate) return 'text-gray-500';
    
    const today = new Date();
    const due = new Date(dueDate);
    const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'text-red-600'; // Overdue
    if (diffDays === 0) return 'text-orange-600'; // Due today
    if (diffDays <= 3) return 'text-yellow-600'; // Due soon
    return 'text-gray-600'; // Normal
  };

  const getAssignedStakeholder = (stakeholderId) => {
    return stakeholders.find(s => s.id === stakeholderId);
  };

  const TaskCard = ({ task, index }) => {
    const assignedStakeholder = getAssignedStakeholder(task.assigned_stakeholder_id);
    const overdue = isOverdue(task.due_date);

    return (
      <Draggable draggableId={task.id.toString()} index={index}>
        {(provided, snapshot) => (
          <Card
            ref={provided.innerRef}
            {...provided.draggableProps}
            {...provided.dragHandleProps}
            className={`mb-3 cursor-pointer transition-all duration-200 hover:shadow-md ${
              snapshot.isDragging ? 'shadow-lg rotate-2' : ''
            } ${overdue ? 'border-red-200 bg-red-50' : ''}`}
            onClick={() => onTaskClick && onTaskClick(task)}
          >
            <CardContent className="p-4">
              {/* Header with priority and actions */}
              <div className="flex items-start justify-between mb-2">
                <Badge className={`${getPriorityColor(task.priority)} text-xs flex items-center gap-1`}>
                  {getPriorityIcon(task.priority)}
                  {task.priority}
                </Badge>
                <div className="flex items-center gap-1">
                  {getStatusIcon(task.status)}
                  {onTaskDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 hover:text-red-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete task "${task.title}"?`)) {
                          onTaskDelete(task.id);
                        }
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Task title */}
              <h4 className="font-medium text-sm mb-2 line-clamp-2">
                {task.title}
              </h4>

              {/* Task description */}
              {task.description && (
                <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                  {task.description}
                </p>
              )}

              {/* Progress bar */}
              {task.progress_percentage > 0 && (
                <div className="mb-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-500">Progress</span>
                    <span className="text-xs font-medium">{task.progress_percentage}%</span>
                  </div>
                  <Progress value={task.progress_percentage} className="h-1" />
                </div>
              )}

              {/* Tags */}
              {task.tags && task.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {task.tags.slice(0, 3).map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs px-1 py-0">
                      {tag}
                    </Badge>
                  ))}
                  {task.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs px-1 py-0">
                      +{task.tags.length - 3}
                    </Badge>
                  )}
                </div>
              )}

              {/* Footer with assignee and due date */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {assignedStakeholder && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Avatar className="h-6 w-6">
                            <AvatarImage src={assignedStakeholder.avatar} />
                            <AvatarFallback className="text-xs">
                              {assignedStakeholder.name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{assignedStakeholder.name}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                  
                  {task.estimated_duration && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <div className="flex items-center gap-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            {Math.round(task.estimated_duration / 60)}h
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Estimated: {task.estimated_duration} minutes</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>

                {task.due_date && (
                  <div className={`flex items-center gap-1 text-xs ${getDueDateColor(task.due_date)}`}>
                    <Calendar className="h-3 w-3" />
                    {format(new Date(task.due_date), 'MMM d')}
                    {overdue && <AlertTriangle className="h-3 w-3 text-red-500" />}
                  </div>
                )}
              </div>

              {/* Subtasks indicator */}
              {task.subtask_count > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Target className="h-3 w-3" />
                    {task.subtask_count} subtask{task.subtask_count !== 1 ? 's' : ''}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </Draggable>
    );
  };

  const ColumnHeader = ({ column }) => {
    const taskCount = column.tasks.length;
    const completedTasks = column.tasks.filter(task => task.status === 'done').length;
    const overdueTasks = column.tasks.filter(task => isOverdue(task.due_date)).length;

    return (
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-sm">{column.title}</h3>
          <Badge variant="secondary" className="text-xs">
            {taskCount}
          </Badge>
          {overdueTasks > 0 && (
            <Badge variant="destructive" className="text-xs">
              {overdueTasks} overdue
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={() => onAddTask && onAddTask(column.id)}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    );
  };

  const getColumnStats = () => {
    const stats = {
      total: 0,
      completed: 0,
      overdue: 0,
      dueToday: 0
    };

    Object.values(columns).forEach(column => {
      stats.total += column.tasks.length;
      stats.completed += column.tasks.filter(task => task.status === 'done').length;
      stats.overdue += column.tasks.filter(task => isOverdue(task.due_date)).length;
      
      const today = format(new Date(), 'yyyy-MM-dd');
      stats.dueToday += column.tasks.filter(task => 
        task.due_date && format(new Date(task.due_date), 'yyyy-MM-dd') === today
      ).length;
    });

    return stats;
  };

  const stats = getColumnStats();

  return (
    <div className={`kanban-board ${className}`}>
      {/* Header with stats and filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold">Task Board</h2>
          <div className="flex gap-3 text-sm">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>{stats.total} total</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>{stats.completed} completed</span>
            </div>
            {stats.overdue > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span>{stats.overdue} overdue</span>
              </div>
            )}
            {stats.dueToday > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <span>{stats.dueToday} due today</span>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <select
            value={filters.priority}
            onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="all">All Priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filters.assignee}
            onChange={(e) => setFilters(prev => ({ ...prev, assignee: e.target.value }))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="all">All Assignees</option>
            {stakeholders.map(stakeholder => (
              <option key={stakeholder.id} value={stakeholder.id}>
                {stakeholder.name}
              </option>
            ))}
          </select>

          <select
            value={filters.dueDate}
            onChange={(e) => setFilters(prev => ({ ...prev, dueDate: e.target.value }))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="all">All Due Dates</option>
            <option value="overdue">Overdue</option>
            <option value="today">Due Today</option>
            <option value="week">Due This Week</option>
          </select>

          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-1" />
            Filter
          </Button>
        </div>
      </div>

      {/* Kanban Board */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.values(columns).map(column => (
            <div key={column.id} className="flex flex-col">
              <div className={`${column.color} rounded-lg p-4 min-h-[600px]`}>
                <ColumnHeader column={column} />
                
                <Droppable droppableId={column.id}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`min-h-[500px] transition-colors duration-200 ${
                        snapshot.isDraggingOver ? 'bg-blue-50 bg-opacity-50' : ''
                      }`}
                    >
                      {column.tasks.map((task, index) => (
                        <TaskCard key={task.id} task={task} index={index} />
                      ))}
                      {provided.placeholder}
                      
                      {/* Empty state */}
                      {column.tasks.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-32 text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
                          <Circle className="h-8 w-8 mb-2" />
                          <p className="text-sm">No tasks</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-2 text-xs"
                            onClick={() => onAddTask && onAddTask(column.id)}
                          >
                            Add a task
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </Droppable>
              </div>
            </div>
          ))}
        </div>
      </DragDropContext>

      {/* Quick Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Total Tasks</p>
                <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
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
                <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <div>
                <p className="text-sm font-medium">Overdue</p>
                <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-orange-600" />
              <div>
                <p className="text-sm font-medium">Due Today</p>
                <p className="text-2xl font-bold text-orange-600">{stats.dueToday}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default KanbanBoard;
