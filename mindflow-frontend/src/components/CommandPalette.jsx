/**
 * CommandPalette - Obsidian-inspired quick action palette (Cmd+K)
 * Provides fast access to all MindFlow actions via keyboard.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from './ui/command';
import {
  CheckSquare, Users, StickyNote, BarChart3, Plus, Search,
  LayoutDashboard, Bot, MessageCircle, Settings, Calendar,
  Zap, Brain, Edit, Trash2, ArrowRight
} from 'lucide-react';

const CommandPalette = ({ 
  onNavigate, 
  onQuickAdd, 
  onOpenAI, 
  tasks = [], 
  stakeholders = [], 
  notes = [],
  currentView 
}) => {
  const [open, setOpen] = useState(false);

  // Keyboard shortcut: Cmd+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const runCommand = useCallback((callback) => {
    setOpen(false);
    callback();
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        
        {/* Quick Actions */}
        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => runCommand(() => onQuickAdd?.())}>
            <Plus className="mr-2 h-4 w-4" />
            <span>Quick Add (Voice/Text)</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onOpenAI?.())}>
            <Bot className="mr-2 h-4 w-4" />
            <span>Ask OpenClaw AI</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onQuickAdd?.('task'))}>
            <CheckSquare className="mr-2 h-4 w-4" />
            <span>Create New Task</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onQuickAdd?.('stakeholder'))}>
            <Users className="mr-2 h-4 w-4" />
            <span>Add New Stakeholder</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onQuickAdd?.('note'))}>
            <StickyNote className="mr-2 h-4 w-4" />
            <span>Create New Note</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        {/* Navigation */}
        <CommandGroup heading="Navigate">
          <CommandItem onSelect={() => runCommand(() => onNavigate?.('dashboard'))}>
            <LayoutDashboard className="mr-2 h-4 w-4" />
            <span>Dashboard</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onNavigate?.('tasks'))}>
            <CheckSquare className="mr-2 h-4 w-4" />
            <span>Tasks</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onNavigate?.('stakeholders'))}>
            <Users className="mr-2 h-4 w-4" />
            <span>Stakeholders</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onNavigate?.('notes'))}>
            <StickyNote className="mr-2 h-4 w-4" />
            <span>Notes</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => onNavigate?.('analytics'))}>
            <BarChart3 className="mr-2 h-4 w-4" />
            <span>Analytics</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        {/* Recent Tasks */}
        {tasks.length > 0 && (
          <CommandGroup heading="Recent Tasks">
            {tasks.filter(t => t.status !== 'done').slice(0, 5).map(task => (
              <CommandItem key={`task-${task.id}`} onSelect={() => runCommand(() => {
                onNavigate?.('tasks');
              })}>
                <CheckSquare className="mr-2 h-4 w-4 text-blue-500" />
                <span>{task.title}</span>
                {task.priority && (
                  <span className={`ml-auto text-xs px-1.5 py-0.5 rounded ${
                    task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                    task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                    task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {task.priority}
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* Recent Stakeholders */}
        {stakeholders.length > 0 && (
          <CommandGroup heading="Stakeholders">
            {stakeholders.slice(0, 5).map(s => (
              <CommandItem key={`sh-${s.id}`} onSelect={() => runCommand(() => {
                onNavigate?.('stakeholders');
              })}>
                <Users className="mr-2 h-4 w-4 text-purple-500" />
                <span>{s.name}</span>
                {s.company && (
                  <span className="ml-auto text-xs text-gray-400">{s.company}</span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* Recent Notes */}
        {notes.length > 0 && (
          <CommandGroup heading="Notes">
            {notes.slice(0, 5).map(n => (
              <CommandItem key={`note-${n.id}`} onSelect={() => runCommand(() => {
                onNavigate?.('notes');
              })}>
                <StickyNote className="mr-2 h-4 w-4 text-yellow-500" />
                <span>{n.title || n.content?.substring(0, 50) || 'Untitled'}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  );
};

export default CommandPalette;
