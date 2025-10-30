import React, { useState, useMemo } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  ChevronLeft, 
  ChevronRight, 
  Calendar as CalendarIcon, 
  Clock, 
  User, 
  AlertTriangle,
  CheckCircle2,
  Plus,
  Filter,
  Eye,
  List,
  Grid3x3
} from 'lucide-react';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const localizer = momentLocalizer(moment);

const TaskCalendar = ({ 
  tasks = [], 
  onTaskClick, 
  onTaskEdit, 
  onTaskCreate, 
  onDateSelect,
  stakeholders = [],
  className = "" 
}) => {
  const [view, setView] = useState('month');
  const [date, setDate] = useState(new Date());
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    priority: 'all',
    status: 'all',
    assignee: 'all'
  });

  // Convert tasks to calendar events
  const events = useMemo(() => {
    return tasks
      .filter(task => {
        // Apply filters
        if (filters.priority !== 'all' && task.priority !== filters.priority) return false;
        if (filters.status !== 'all' && task.status !== filters.status) return false;
        if (filters.assignee !== 'all' && task.assigned_stakeholder_id !== parseInt(filters.assignee)) return false;
        return true;
      })
      .map(task => {
        const startDate = task.start_date ? new Date(task.start_date) : new Date(task.created_at);
        const endDate = task.due_date ? new Date(task.due_date) : startDate;
        
        // If task has estimated duration, use it for end time
        let calculatedEndDate = endDate;
        if (task.estimated_duration && task.start_date) {
          calculatedEndDate = new Date(startDate.getTime() + (task.estimated_duration * 60 * 1000));
        }

        return {
          id: task.id,
          title: task.title,
          start: startDate,
          end: calculatedEndDate,
          resource: task,
          allDay: !task.start_date || !task.estimated_duration
        };
      });
  }, [tasks, filters]);

  // Custom event component
  const EventComponent = ({ event }) => {
    const task = event.resource;
    const assignedStakeholder = stakeholders.find(s => s.id === task.assigned_stakeholder_id);
    
    const getPriorityColor = (priority) => {
      const colors = {
        urgent: 'bg-red-500 border-red-600',
        high: 'bg-orange-500 border-orange-600',
        medium: 'bg-yellow-500 border-yellow-600',
        low: 'bg-green-500 border-green-600'
      };
      return colors[priority] || colors.medium;
    };

    const getStatusIcon = (status) => {
      switch (status) {
        case 'done':
          return <CheckCircle2 className="h-3 w-3 text-white" />;
        case 'in_progress':
          return <Clock className="h-3 w-3 text-white" />;
        default:
          return null;
      }
    };

    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div 
              className={`
                p-1 rounded text-white text-xs cursor-pointer
                ${getPriorityColor(task.priority)}
                ${isOverdue ? 'animate-pulse' : ''}
                hover:opacity-90 transition-opacity
              `}
              onClick={() => onTaskClick && onTaskClick(task)}
            >
              <div className="flex items-center gap-1 truncate">
                {getStatusIcon(task.status)}
                <span className="truncate">{task.title}</span>
                {isOverdue && <AlertTriangle className="h-3 w-3 flex-shrink-0" />}
              </div>
              {assignedStakeholder && (
                <div className="text-xs opacity-75 truncate">
                  {assignedStakeholder.name}
                </div>
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="space-y-1">
              <p className="font-medium">{task.title}</p>
              {task.description && (
                <p className="text-sm opacity-90 line-clamp-2">{task.description}</p>
              )}
              <div className="flex items-center gap-2 text-xs">
                <Badge variant="outline" className="text-xs">
                  {task.priority}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {task.status}
                </Badge>
              </div>
              {assignedStakeholder && (
                <div className="flex items-center gap-1 text-xs">
                  <User className="h-3 w-3" />
                  {assignedStakeholder.name}
                </div>
              )}
              {task.estimated_duration && (
                <div className="flex items-center gap-1 text-xs">
                  <Clock className="h-3 w-3" />
                  {Math.round(task.estimated_duration / 60)}h estimated
                </div>
              )}
              {task.due_date && (
                <div className="text-xs">
                  Due: {moment(task.due_date).format('MMM D, YYYY h:mm A')}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  };

  // Custom toolbar
  const CustomToolbar = ({ label, onNavigate, onView }) => {
    return (
      <div className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => onNavigate('PREV')}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => onNavigate('TODAY')}>
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={() => onNavigate('NEXT')}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          <h3 className="text-lg font-semibold ml-4">{label}</h3>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? "default" : "outline"}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-1" />
            Filters
          </Button>
          
          <div className="flex border rounded-md">
            <Button
              variant={view === 'month' ? "default" : "ghost"}
              size="sm"
              className="rounded-r-none"
              onClick={() => onView('month')}
            >
              <Grid3x3 className="h-4 w-4 mr-1" />
              Month
            </Button>
            <Button
              variant={view === 'week' ? "default" : "ghost"}
              size="sm"
              className="rounded-none border-x"
              onClick={() => onView('week')}
            >
              <List className="h-4 w-4 mr-1" />
              Week
            </Button>
            <Button
              variant={view === 'day' ? "default" : "ghost"}
              size="sm"
              className="rounded-l-none"
              onClick={() => onView('day')}
            >
              <Eye className="h-4 w-4 mr-1" />
              Day
            </Button>
          </div>
        </div>
      </div>
    );
  };

  // Get calendar stats
  const getCalendarStats = () => {
    const today = new Date();
    const startOfWeek = moment().startOf('week').toDate();
    const endOfWeek = moment().endOf('week').toDate();
    
    const stats = {
      total: tasks.length,
      today: tasks.filter(task => {
        const taskDate = task.due_date ? new Date(task.due_date) : new Date(task.created_at);
        return moment(taskDate).isSame(today, 'day');
      }).length,
      thisWeek: tasks.filter(task => {
        const taskDate = task.due_date ? new Date(task.due_date) : new Date(task.created_at);
        return taskDate >= startOfWeek && taskDate <= endOfWeek;
      }).length,
      overdue: tasks.filter(task => {
        return task.due_date && new Date(task.due_date) < today && task.status !== 'done';
      }).length,
      completed: tasks.filter(task => task.status === 'done').length
    };

    return stats;
  };

  const stats = getCalendarStats();

  // Custom date cell wrapper for month view
  const DateCellWrapper = ({ children, value }) => {
    const dayTasks = events.filter(event => 
      moment(event.start).isSame(value, 'day') || 
      moment(event.end).isSame(value, 'day')
    );

    const hasOverdue = dayTasks.some(event => {
      const task = event.resource;
      return task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
    });

    const hasHighPriority = dayTasks.some(event => 
      event.resource.priority === 'urgent' || event.resource.priority === 'high'
    );

    return (
      <div className={`
        relative h-full
        ${hasOverdue ? 'bg-red-50' : ''}
        ${hasHighPriority && !hasOverdue ? 'bg-orange-50' : ''}
      `}>
        {children}
        {dayTasks.length > 0 && (
          <div className="absolute top-1 right-1">
            <Badge variant="secondary" className="text-xs h-4 px-1">
              {dayTasks.length}
            </Badge>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`task-calendar ${className}`}>
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Total Tasks</p>
                <p className="text-xl font-bold text-blue-600">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm font-medium">Today</p>
                <p className="text-xl font-bold text-green-600">{stats.today}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-purple-600" />
              <div>
                <p className="text-sm font-medium">This Week</p>
                <p className="text-xl font-bold text-purple-600">{stats.thisWeek}</p>
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
                <p className="text-xl font-bold text-red-600">{stats.overdue}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-xl font-bold text-emerald-600">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-sm">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block">Priority</label>
                <select
                  value={filters.priority}
                  onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full text-sm border rounded px-2 py-1"
                >
                  <option value="all">All Priorities</option>
                  <option value="urgent">Urgent</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full text-sm border rounded px-2 py-1"
                >
                  <option value="all">All Statuses</option>
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="waiting">Waiting</option>
                  <option value="done">Done</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">Assignee</label>
                <select
                  value={filters.assignee}
                  onChange={(e) => setFilters(prev => ({ ...prev, assignee: e.target.value }))}
                  className="w-full text-sm border rounded px-2 py-1"
                >
                  <option value="all">All Assignees</option>
                  {stakeholders.map(stakeholder => (
                    <option key={stakeholder.id} value={stakeholder.id}>
                      {stakeholder.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calendar */}
      <Card>
        <CardContent className="p-0">
          <div style={{ height: '600px' }}>
            <Calendar
              localizer={localizer}
              events={events}
              startAccessor="start"
              endAccessor="end"
              view={view}
              onView={setView}
              date={date}
              onNavigate={setDate}
              onSelectEvent={(event) => onTaskClick && onTaskClick(event.resource)}
              onSelectSlot={(slotInfo) => onDateSelect && onDateSelect(slotInfo)}
              selectable
              components={{
                event: EventComponent,
                toolbar: CustomToolbar,
                dateCellWrapper: DateCellWrapper
              }}
              eventPropGetter={(event) => {
                const task = event.resource;
                const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
                
                return {
                  className: isOverdue ? 'overdue-event' : '',
                  style: {
                    backgroundColor: 'transparent',
                    border: 'none',
                    padding: 0
                  }
                };
              }}
              dayPropGetter={(date) => {
                const isToday = moment(date).isSame(new Date(), 'day');
                const dayEvents = events.filter(event => 
                  moment(event.start).isSame(date, 'day')
                );
                const hasOverdue = dayEvents.some(event => {
                  const task = event.resource;
                  return task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
                });

                return {
                  className: `
                    ${isToday ? 'today' : ''}
                    ${hasOverdue ? 'has-overdue' : ''}
                  `,
                  style: isToday ? {
                    backgroundColor: '#EBF8FF'
                  } : {}
                };
              }}
              formats={{
                timeGutterFormat: 'HH:mm',
                eventTimeRangeFormat: ({ start, end }) => {
                  return `${moment(start).format('HH:mm')} - ${moment(end).format('HH:mm')}`;
                },
                dayHeaderFormat: 'dddd MMM DD',
                dayRangeHeaderFormat: ({ start, end }) => {
                  return `${moment(start).format('MMM DD')} - ${moment(end).format('MMM DD, YYYY')}`;
                }
              }}
              step={30}
              timeslots={2}
              min={new Date(2024, 0, 1, 8, 0)} // 8 AM
              max={new Date(2024, 0, 1, 20, 0)} // 8 PM
            />
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-sm">Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span>Urgent Priority</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span>High Priority</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <span>Medium Priority</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>Low Priority</span>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            • Overdue tasks have a pulsing animation
            • Click on tasks to view details
            • Click on empty dates to create new tasks
          </div>
        </CardContent>
      </Card>

      {/* Custom CSS for calendar styling */}
      <style jsx global>{`
        .rbc-calendar {
          font-family: inherit;
        }
        
        .rbc-toolbar {
          display: none; /* We use custom toolbar */
        }
        
        .rbc-month-view .rbc-date-cell {
          padding: 4px;
        }
        
        .rbc-event {
          padding: 0 !important;
          border: none !important;
          background: transparent !important;
        }
        
        .today .rbc-date-cell {
          background-color: #EBF8FF !important;
        }
        
        .has-overdue .rbc-date-cell {
          border-left: 3px solid #EF4444;
        }
        
        .overdue-event {
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        
        .rbc-month-view .rbc-day-bg.rbc-today {
          background-color: #EBF8FF;
        }
        
        .rbc-time-view .rbc-current-time-indicator {
          background-color: #EF4444;
          height: 2px;
        }
      `}</style>
    </div>
  );
};

export default TaskCalendar;
