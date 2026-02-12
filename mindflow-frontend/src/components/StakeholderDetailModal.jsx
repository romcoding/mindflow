import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Building2, 
  Mail, 
  Phone, 
  Calendar, 
  MapPin, 
  Globe, 
  Linkedin, 
  Twitter,
  Heart,
  TrendingUp,
  Shield,
  Clock,
  Users,
  MessageCircle,
  Star,
  Target,
  AlertTriangle,
  Briefcase,
  GraduationCap,
  Save,
  X,
  Plus,
  Trash2,
  Loader2
} from 'lucide-react';
import { linkedinAPI } from '@/lib/api';

const StakeholderDetailModal = ({ 
  isOpen, 
  onClose, 
  stakeholder, 
  onSave, 
  onDelete,
  isEditing = false 
}) => {
  const [formData, setFormData] = useState({
    // Basic Information
    name: '',
    role: '',
    company: '',
    department: '',
    job_title: '',
    
    // Contact Information
    email: '',
    phone: '',
    linkedin_url: '',
    twitter_handle: '',
    
    // Personal Information
    birthday: '',
    family_info: '',
    hobbies: '',
    personal_notes: '',
    education: '',
    career_history: '',
    
    // Professional Details
    seniority_level: 'mid',
    years_experience: 0,
    specializations: [],
    decision_making_authority: 'low',
    budget_authority: 'none',
    work_style: '',
    
    // Geographic and Cultural
    location: '',
    timezone: '',
    preferred_language: 'English',
    cultural_background: '',
    
    // Communication Preferences
    preferred_communication_method: 'email',
    communication_frequency: 'weekly',
    best_contact_time: '',
    communication_style: '',
    
    // Relationship Mapping
    sentiment: 'neutral',
    influence: 5,
    interest: 5,
    trust_level: 5,
    
    // Strategic Importance
    strategic_value: 'medium',
    risk_level: 'low',
    opportunity_potential: 'medium',
    
    // Project Context
    current_projects: [],
    availability_status: 'available',
    collaboration_history: '',
    conflict_resolution_style: '',
    
    // Tags
    tags: []
  });

  const [newTag, setNewTag] = useState('');
  const [newSpecialization, setNewSpecialization] = useState('');
  const [newProject, setNewProject] = useState('');
  const [isFetchingLinkedIn, setIsFetchingLinkedIn] = useState(false);

  // Initialize form data when stakeholder changes
  useEffect(() => {
    if (stakeholder) {
      setFormData({
        name: stakeholder.name || '',
        role: stakeholder.role || '',
        company: stakeholder.company || '',
        department: stakeholder.department || '',
        job_title: stakeholder.job_title || '',
        email: stakeholder.email || '',
        phone: stakeholder.phone || '',
        linkedin_url: stakeholder.linkedin_url || '',
        twitter_handle: stakeholder.twitter_handle || '',
        birthday: stakeholder.birthday || '',
        family_info: stakeholder.family_info || '',
        hobbies: stakeholder.hobbies || '',
        personal_notes: stakeholder.personal_notes || '',
        education: stakeholder.education || '',
        career_history: stakeholder.career_history || '',
        seniority_level: stakeholder.seniority_level || 'mid',
        years_experience: stakeholder.years_experience || 0,
        specializations: stakeholder.specializations || [],
        decision_making_authority: stakeholder.decision_making_authority || 'low',
        budget_authority: stakeholder.budget_authority || 'none',
        work_style: stakeholder.work_style || '',
        location: stakeholder.location || '',
        timezone: stakeholder.timezone || '',
        preferred_language: stakeholder.preferred_language || 'English',
        cultural_background: stakeholder.cultural_background || '',
        preferred_communication_method: stakeholder.preferred_communication_method || 'email',
        communication_frequency: stakeholder.communication_frequency || 'weekly',
        best_contact_time: stakeholder.best_contact_time || '',
        communication_style: stakeholder.communication_style || '',
        sentiment: stakeholder.sentiment || 'neutral',
        influence: stakeholder.influence || 5,
        interest: stakeholder.interest || 5,
        trust_level: stakeholder.trust_level || 5,
        strategic_value: stakeholder.strategic_value || 'medium',
        risk_level: stakeholder.risk_level || 'low',
        opportunity_potential: stakeholder.opportunity_potential || 'medium',
        current_projects: stakeholder.current_projects || [],
        availability_status: stakeholder.availability_status || 'available',
        collaboration_history: stakeholder.collaboration_history || '',
        conflict_resolution_style: stakeholder.conflict_resolution_style || '',
        tags: stakeholder.tags || []
      });
    }
  }, [stakeholder]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSliderChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value[0]
    }));
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const addSpecialization = () => {
    if (newSpecialization.trim() && !formData.specializations.includes(newSpecialization.trim())) {
      setFormData(prev => ({
        ...prev,
        specializations: [...prev.specializations, newSpecialization.trim()]
      }));
      setNewSpecialization('');
    }
  };

  const removeSpecialization = (specToRemove) => {
    setFormData(prev => ({
      ...prev,
      specializations: prev.specializations.filter(spec => spec !== specToRemove)
    }));
  };

  const addProject = () => {
    if (newProject.trim() && !formData.current_projects.includes(newProject.trim())) {
      setFormData(prev => ({
        ...prev,
        current_projects: [...prev.current_projects, newProject.trim()]
      }));
      setNewProject('');
    }
  };

  const removeProject = (projectToRemove) => {
    setFormData(prev => ({
      ...prev,
      current_projects: prev.current_projects.filter(project => project !== projectToRemove)
    }));
  };

  const handleFetchLinkedIn = async () => {
    if (!formData.linkedin_url && !formData.name) {
      alert('Please provide either a LinkedIn URL or a name to fetch profile data.');
      return;
    }

    setIsFetchingLinkedIn(true);
    try {
      const response = await linkedinAPI.fetchProfile({
        linkedin_url: formData.linkedin_url || null,
        name: formData.name || null,
        company: formData.company || null
      });

      if (response.data?.success && response.data?.stakeholder_info) {
        const linkedinData = response.data.stakeholder_info;
        
        // Update form data with LinkedIn information (only fill empty fields)
        setFormData(prev => ({
          ...prev,
          name: prev.name || linkedinData.name || prev.name,
          company: prev.company || linkedinData.company || prev.company,
          role: prev.role || linkedinData.role || prev.role,
          job_title: prev.job_title || linkedinData.job_title || prev.job_title,
          location: prev.location || linkedinData.location || prev.location,
          linkedin_url: prev.linkedin_url || linkedinData.linkedin_url || prev.linkedin_url,
          email: prev.email || linkedinData.email || prev.email,
          phone: prev.phone || linkedinData.phone || prev.phone,
          personal_notes: prev.personal_notes 
            ? `${prev.personal_notes}\n\nLinkedIn: ${linkedinData.personal_notes || ''}`.trim()
            : linkedinData.personal_notes || prev.personal_notes,
          education: prev.education || linkedinData.education || prev.education,
        }));
        
        alert('LinkedIn profile data fetched and populated successfully!');
      } else {
        const errorMsg = response.data?.error || response.data?.message || 'Failed to fetch LinkedIn profile';
        alert(errorMsg);
      }
    } catch (error) {
      console.error('Failed to fetch LinkedIn profile:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message || 'Failed to fetch LinkedIn profile';
      alert(errorMsg);
    } finally {
      setIsFetchingLinkedIn(false);
    }
  };

  const handleSave = () => {
    onSave(formData);
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      positive: 'bg-green-100 text-green-800',
      neutral: 'bg-gray-100 text-gray-800',
      negative: 'bg-red-100 text-red-800'
    };
    return colors[sentiment] || colors.neutral;
  };

  const getInfluenceLabel = (influence) => {
    if (influence >= 8) return 'High';
    if (influence >= 6) return 'Medium-High';
    if (influence >= 4) return 'Medium';
    return 'Low';
  };

  const formatBirthday = (birthday) => {
    if (!birthday) return 'Not specified';
    try {
      const date = new Date(birthday);
      return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
    } catch {
      return birthday;
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            {isEditing ? 'Edit Stakeholder' : (stakeholder ? stakeholder.name : 'New Stakeholder')}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-5 gap-1">
            <TabsTrigger value="basic" className="text-xs px-2">Basic</TabsTrigger>
            <TabsTrigger value="professional" className="text-xs px-2">Professional</TabsTrigger>
            <TabsTrigger value="personal" className="text-xs px-2">Personal</TabsTrigger>
            <TabsTrigger value="communication" className="text-xs px-1">Comm.</TabsTrigger>
            <TabsTrigger value="relationship" className="text-xs px-1">Relation</TabsTrigger>
          </TabsList>

          {/* Basic Information Tab */}
          <TabsContent value="basic" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Basic Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="name">Full Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="Enter full name"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="role">Role/Position</Label>
                    <Input
                      id="role"
                      value={formData.role}
                      onChange={(e) => handleInputChange('role', e.target.value)}
                      placeholder="e.g., Product Manager"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      value={formData.company}
                      onChange={(e) => handleInputChange('company', e.target.value)}
                      placeholder="Company name"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="department">Department</Label>
                    <Input
                      id="department"
                      value={formData.department}
                      onChange={(e) => handleInputChange('department', e.target.value)}
                      placeholder="e.g., Engineering, Marketing"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="email@company.com"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="phone">Phone</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="+1 (555) 123-4567"
                        className="pl-10"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="location">Location</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="location"
                        value={formData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        placeholder="City, Country"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="timezone">Timezone</Label>
                    <Input
                      id="timezone"
                      value={formData.timezone}
                      onChange={(e) => handleInputChange('timezone', e.target.value)}
                      placeholder="e.g., EST, PST, UTC+1"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Professional Information Tab */}
          <TabsContent value="professional" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4" />
                  Professional Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="job_title">Job Title</Label>
                    <Input
                      id="job_title"
                      value={formData.job_title}
                      onChange={(e) => handleInputChange('job_title', e.target.value)}
                      placeholder="Official job title"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="seniority_level">Seniority Level</Label>
                    <Select value={formData.seniority_level} onValueChange={(value) => handleInputChange('seniority_level', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="intern">Intern</SelectItem>
                        <SelectItem value="junior">Junior</SelectItem>
                        <SelectItem value="mid">Mid-level</SelectItem>
                        <SelectItem value="senior">Senior</SelectItem>
                        <SelectItem value="lead">Lead</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="director">Director</SelectItem>
                        <SelectItem value="vp">VP</SelectItem>
                        <SelectItem value="executive">Executive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="years_experience">Years of Experience</Label>
                    <Input
                      id="years_experience"
                      type="number"
                      value={formData.years_experience}
                      onChange={(e) => handleInputChange('years_experience', parseInt(e.target.value) || 0)}
                      placeholder="0"
                      min="0"
                      max="50"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="work_style">Work Style</Label>
                    <Input
                      id="work_style"
                      value={formData.work_style}
                      onChange={(e) => handleInputChange('work_style', e.target.value)}
                      placeholder="e.g., Collaborative, Independent"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="decision_making_authority">Decision Making Authority</Label>
                    <Select value={formData.decision_making_authority} onValueChange={(value) => handleInputChange('decision_making_authority', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="budget_authority">Budget Authority</Label>
                    <Select value={formData.budget_authority} onValueChange={(value) => handleInputChange('budget_authority', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="limited">Limited</SelectItem>
                        <SelectItem value="significant">Significant</SelectItem>
                        <SelectItem value="full">Full</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>Specializations/Skills</Label>
                  <div className="flex gap-2 mb-2">
                    <Input
                      value={newSpecialization}
                      onChange={(e) => setNewSpecialization(e.target.value)}
                      placeholder="Add a specialization"
                      onKeyPress={(e) => e.key === 'Enter' && addSpecialization()}
                    />
                    <Button type="button" onClick={addSpecialization} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formData.specializations.map((spec, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {spec}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => removeSpecialization(spec)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="career_history">Career History</Label>
                  <Textarea
                    id="career_history"
                    value={formData.career_history}
                    onChange={(e) => handleInputChange('career_history', e.target.value)}
                    placeholder="Brief overview of career progression..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Personal Information Tab */}
          <TabsContent value="personal" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="h-4 w-4" />
                  Personal Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="birthday">Birthday</Label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="birthday"
                        type="date"
                        value={formData.birthday}
                        onChange={(e) => handleInputChange('birthday', e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="preferred_language">Preferred Language</Label>
                    <Input
                      id="preferred_language"
                      value={formData.preferred_language}
                      onChange={(e) => handleInputChange('preferred_language', e.target.value)}
                      placeholder="English"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="family_info">Family Information</Label>
                  <Textarea
                    id="family_info"
                    value={formData.family_info}
                    onChange={(e) => handleInputChange('family_info', e.target.value)}
                    placeholder="Spouse, children, family details..."
                    rows={2}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="hobbies">Hobbies & Interests</Label>
                  <Textarea
                    id="hobbies"
                    value={formData.hobbies}
                    onChange={(e) => handleInputChange('hobbies', e.target.value)}
                    placeholder="Personal interests, hobbies, activities..."
                    rows={2}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="education">Education</Label>
                  <Textarea
                    id="education"
                    value={formData.education}
                    onChange={(e) => handleInputChange('education', e.target.value)}
                    placeholder="Educational background, degrees, certifications..."
                    rows={2}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="cultural_background">Cultural Background</Label>
                  <Input
                    id="cultural_background"
                    value={formData.cultural_background}
                    onChange={(e) => handleInputChange('cultural_background', e.target.value)}
                    placeholder="Cultural or ethnic background"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="personal_notes">Personal Notes</Label>
                  <Textarea
                    id="personal_notes"
                    value={formData.personal_notes}
                    onChange={(e) => handleInputChange('personal_notes', e.target.value)}
                    placeholder="Additional personal information, preferences, notes..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Communication Tab */}
          <TabsContent value="communication" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-4 w-4" />
                  Communication Preferences
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="preferred_communication_method">Preferred Method</Label>
                    <Select value={formData.preferred_communication_method} onValueChange={(value) => handleInputChange('preferred_communication_method', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="email">Email</SelectItem>
                        <SelectItem value="phone">Phone</SelectItem>
                        <SelectItem value="slack">Slack</SelectItem>
                        <SelectItem value="teams">Microsoft Teams</SelectItem>
                        <SelectItem value="zoom">Zoom</SelectItem>
                        <SelectItem value="in_person">In Person</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="communication_frequency">Frequency</Label>
                    <Select value={formData.communication_frequency} onValueChange={(value) => handleInputChange('communication_frequency', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="biweekly">Bi-weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="quarterly">Quarterly</SelectItem>
                        <SelectItem value="as_needed">As Needed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="best_contact_time">Best Contact Time</Label>
                    <Input
                      id="best_contact_time"
                      value={formData.best_contact_time}
                      onChange={(e) => handleInputChange('best_contact_time', e.target.value)}
                      placeholder="e.g., 9-11 AM EST"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="communication_style">Communication Style</Label>
                    <Select value={formData.communication_style} onValueChange={(value) => handleInputChange('communication_style', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select style" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="formal">Formal</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="direct">Direct</SelectItem>
                        <SelectItem value="diplomatic">Diplomatic</SelectItem>
                        <SelectItem value="analytical">Analytical</SelectItem>
                        <SelectItem value="collaborative">Collaborative</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="linkedin_url">LinkedIn Profile</Label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Linkedin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="linkedin_url"
                          value={formData.linkedin_url}
                          onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
                          placeholder="https://linkedin.com/in/username"
                          className="pl-10"
                        />
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={handleFetchLinkedIn}
                        disabled={isFetchingLinkedIn || (!formData.linkedin_url && !formData.name)}
                        title="Fetch LinkedIn profile data"
                        className="shrink-0"
                      >
                        {isFetchingLinkedIn ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Linkedin className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="twitter_handle">Twitter Handle</Label>
                    <div className="relative">
                      <Twitter className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="twitter_handle"
                        value={formData.twitter_handle}
                        onChange={(e) => handleInputChange('twitter_handle', e.target.value)}
                        placeholder="@username"
                        className="pl-10"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Relationship Tab */}
          <TabsContent value="relationship" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Relationship Mapping
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <Label>Sentiment</Label>
                    <Select value={formData.sentiment} onValueChange={(value) => handleInputChange('sentiment', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="positive">Positive</SelectItem>
                        <SelectItem value="neutral">Neutral</SelectItem>
                        <SelectItem value="negative">Negative</SelectItem>
                      </SelectContent>
                    </Select>
                    <Badge className={`mt-2 ${getSentimentColor(formData.sentiment)}`}>
                      {formData.sentiment.charAt(0).toUpperCase() + formData.sentiment.slice(1)}
                    </Badge>
                  </div>

                  <div className="space-y-1.5">
                    <Label>Availability Status</Label>
                    <Select value={formData.availability_status} onValueChange={(value) => handleInputChange('availability_status', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="available">Available</SelectItem>
                        <SelectItem value="busy">Busy</SelectItem>
                        <SelectItem value="unavailable">Unavailable</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <Label>Influence Level: {formData.influence}/10 ({getInfluenceLabel(formData.influence)})</Label>
                    <Slider
                      value={[formData.influence]}
                      onValueChange={(value) => handleSliderChange('influence', value)}
                      max={10}
                      min={1}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label>Interest Level: {formData.interest}/10</Label>
                    <Slider
                      value={[formData.interest]}
                      onValueChange={(value) => handleSliderChange('interest', value)}
                      max={10}
                      min={1}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label>Trust Level: {formData.trust_level}/10</Label>
                    <Slider
                      value={[formData.trust_level]}
                      onValueChange={(value) => handleSliderChange('trust_level', value)}
                      max={10}
                      min={1}
                      step={1}
                      className="mt-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="strategic_value">Strategic Value</Label>
                    <Select value={formData.strategic_value} onValueChange={(value) => handleInputChange('strategic_value', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="risk_level">Risk Level</Label>
                    <Select value={formData.risk_level} onValueChange={(value) => handleInputChange('risk_level', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="opportunity_potential">Opportunity</Label>
                    <Select value={formData.opportunity_potential} onValueChange={(value) => handleInputChange('opportunity_potential', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>Current Projects</Label>
                  <div className="flex gap-2 mb-2">
                    <Input
                      value={newProject}
                      onChange={(e) => setNewProject(e.target.value)}
                      placeholder="Add a project"
                      onKeyPress={(e) => e.key === 'Enter' && addProject()}
                    />
                    <Button type="button" onClick={addProject} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formData.current_projects.map((project, index) => (
                      <Badge key={index} variant="outline" className="flex items-center gap-1">
                        {project}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => removeProject(project)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="collaboration_history">Collaboration History</Label>
                  <Textarea
                    id="collaboration_history"
                    value={formData.collaboration_history}
                    onChange={(e) => handleInputChange('collaboration_history', e.target.value)}
                    placeholder="Past collaborations, projects worked on together..."
                    rows={2}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label>Tags</Label>
                  <div className="flex gap-2 mb-2">
                    <Input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      placeholder="Add a tag"
                      onKeyPress={(e) => e.key === 'Enter' && addTag()}
                    />
                    <Button type="button" onClick={addTag} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {tag}
                        <X
                          className="h-3 w-3 cursor-pointer"
                          onClick={() => removeTag(tag)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4 border-t">
          <div>
            {onDelete && stakeholder && (
              <Button
                variant="destructive"
                onClick={() => {
                  if (window.confirm(`Delete stakeholder "${formData.name}"? This cannot be undone.`)) {
                    onDelete(stakeholder.id);
                  }
                }}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSave} className="flex items-center gap-2">
              <Save className="h-4 w-4" />
              Save Stakeholder
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default StakeholderDetailModal;
