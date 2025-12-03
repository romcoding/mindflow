import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ZoomIn, ZoomOut, RotateCcw, Users, Network, Filter, X } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const StakeholderNetworkMap = ({ 
  stakeholders = [], 
  relationships = [], 
  onNodeClick, 
  selectedNodeId = null,
  className = "" 
}) => {
  const svgRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [simulation, setSimulation] = useState(null);
  const [transform, setTransform] = useState(d3.zoomIdentity);
  const [selectedFilters, setSelectedFilters] = useState({
    sentiment: 'all',
    influence: 'all',
    company: 'all',
    role: 'all',
    strategic_value: 'all',
    trust_level: 'all',
    relationship_type: 'all'
  });

  // Process data for D3 with filters
  const processData = () => {
    // Filter stakeholders based on selected filters
    let filteredStakeholders = stakeholders.filter(stakeholder => {
      if (selectedFilters.sentiment !== 'all' && stakeholder.sentiment !== selectedFilters.sentiment) return false;
      if (selectedFilters.company !== 'all' && (stakeholder.company || 'Unknown') !== selectedFilters.company) return false;
      if (selectedFilters.role !== 'all' && (stakeholder.role || 'Unknown') !== selectedFilters.role) return false;
      if (selectedFilters.strategic_value !== 'all' && (stakeholder.strategic_value || 'medium') !== selectedFilters.strategic_value) return false;
      if (selectedFilters.trust_level !== 'all') {
        const trustLevel = stakeholder.trust_level || 5;
        const filterLevel = parseInt(selectedFilters.trust_level);
        if (filterLevel === 1 && trustLevel < 3) return true;
        if (filterLevel === 2 && trustLevel >= 3 && trustLevel < 6) return true;
        if (filterLevel === 3 && trustLevel >= 6 && trustLevel < 8) return true;
        if (filterLevel === 4 && trustLevel >= 8) return true;
        return false;
      }
      if (selectedFilters.influence !== 'all') {
        const influence = stakeholder.influence || 5;
        const filterInfluence = parseInt(selectedFilters.influence);
        if (filterInfluence === 1 && influence < 3) return true;
        if (filterInfluence === 2 && influence >= 3 && influence < 6) return true;
        if (filterInfluence === 3 && influence >= 6 && influence < 8) return true;
        if (filterInfluence === 4 && influence >= 8) return true;
        return false;
      }
      return true;
    });

    // Filter relationships based on relationship type filter
    let filteredRelationships = relationships;
    if (selectedFilters.relationship_type !== 'all') {
      filteredRelationships = relationships.filter(rel => 
        rel.relationship_type === selectedFilters.relationship_type
      );
    }

    // Only include relationships between filtered stakeholders
    const filteredStakeholderIds = new Set(filteredStakeholders.map(s => s.id.toString()));
    filteredRelationships = filteredRelationships.filter(rel => 
      filteredStakeholderIds.has(rel.source_stakeholder_id.toString()) &&
      filteredStakeholderIds.has(rel.target_stakeholder_id.toString())
    );

    // Create nodes from filtered stakeholders
    const nodes = filteredStakeholders.map(stakeholder => ({
      id: stakeholder.id.toString(),
      name: stakeholder.name,
      role: stakeholder.role || 'Unknown',
      company: stakeholder.company || 'Unknown',
      sentiment: stakeholder.sentiment || 'neutral',
      influence: stakeholder.influence || 5,
      interest: stakeholder.interest || 5,
      strategic_value: stakeholder.strategic_value || 'medium',
      trust_level: stakeholder.trust_level || 5,
      email: stakeholder.email,
      phone: stakeholder.phone,
      // Visual properties
      radius: Math.max(8, Math.min(25, (stakeholder.influence || 5) * 2.5)),
      color: getSentimentColor(stakeholder.sentiment),
      strokeColor: getInfluenceStrokeColor(stakeholder.influence),
      strokeWidth: getInfluenceStrokeWidth(stakeholder.influence)
    }));

    // Create links from filtered relationships
    const links = filteredRelationships
      .filter(rel => rel.is_active !== false)
      .map(rel => ({
        source: rel.source_stakeholder_id.toString(),
        target: rel.target_stakeholder_id.toString(),
        relationship_type: rel.relationship_type,
        strength: rel.relationship_strength || 5,
        context: rel.context,
        direction: rel.direction || 'bidirectional',
        strokeWidth: Math.max(1, (rel.relationship_strength || 5) / 2),
        color: getRelationshipColor(rel.relationship_type)
      }));

    return { nodes, links };
  };

  // Color mapping functions
  const getSentimentColor = (sentiment) => {
    const colors = {
      positive: '#10B981',
      neutral: '#6B7280',
      negative: '#EF4444',
      unknown: '#9CA3AF'
    };
    return colors[sentiment] || colors.neutral;
  };

  const getInfluenceStrokeColor = (influence) => {
    if (influence >= 8) return '#DC2626'; // High influence - red
    if (influence >= 6) return '#F59E0B'; // Medium-high influence - amber
    if (influence >= 4) return '#3B82F6'; // Medium influence - blue
    return '#6B7280'; // Low influence - gray
  };

  const getInfluenceStrokeWidth = (influence) => {
    if (influence >= 8) return 3;
    if (influence >= 6) return 2;
    return 1;
  };

  const getRelationshipColor = (type) => {
    const colors = {
      boss: '#DC2626',
      employee: '#059669',
      colleague: '#3B82F6',
      client: '#7C3AED',
      partner: '#DB2777',
      family: '#F59E0B',
      friend: '#10B981',
      mentor: '#8B5CF6',
      mentee: '#06B6D4'
    };
    return colors[type] || '#6B7280';
  };

  // Initialize and update D3 visualization
  useEffect(() => {
    if (!stakeholders.length) return;

    const { nodes, links } = processData();
    const svg = d3.select(svgRef.current);
    const container = svg.select('.network-container');

    // Clear previous content
    container.selectAll('*').remove();

    // Create groups for links and nodes
    const linkGroup = container.append('g').attr('class', 'links');
    const nodeGroup = container.append('g').attr('class', 'nodes');

    // Group nodes by company for clustering
    const companyGroups = {};
    nodes.forEach(node => {
      const company = node.company || 'Unknown';
      if (!companyGroups[company]) {
        companyGroups[company] = [];
      }
      companyGroups[company].push(node);
    });

    // Create force simulation with company clustering
    const newSimulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id)
        .distance(d => {
          // Shorter distance for same company, longer for different companies
          const sourceNode = nodes.find(n => n.id === (typeof d.source === 'object' ? d.source.id : d.source));
          const targetNode = nodes.find(n => n.id === (typeof d.target === 'object' ? d.target.id : d.target));
          const sourceCompany = sourceNode?.company || 'Unknown';
          const targetCompany = targetNode?.company || 'Unknown';
          return sourceCompany === targetCompany ? 80 : 150;
        })
        .strength(d => {
          // Stronger links for higher relationship strength
          return (d.strength || 5) / 10;
        }))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
      .force('collision', d3.forceCollide().radius(d => d.radius + 5))
      .force('x', d3.forceX().strength(0.1).x(d => {
        // Cluster by company on X axis
        const company = d.company || 'Unknown';
        const companyIndex = Object.keys(companyGroups).indexOf(company);
        const totalCompanies = Object.keys(companyGroups).length;
        return (companyIndex + 1) * (dimensions.width / (totalCompanies + 1));
      }))
      .force('y', d3.forceY().strength(0.1).y(dimensions.height / 2));

    // Create links with enhanced visualization
    const link = linkGroup
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', d => d.color)
      .attr('stroke-width', d => {
        // Thicker lines for stronger relationships
        return Math.max(1, Math.min(5, (d.strength || 5) / 2));
      })
      .attr('stroke-opacity', d => {
        // More opaque for stronger relationships
        return 0.3 + ((d.strength || 5) / 10) * 0.5;
      })
      .attr('marker-end', d => d.direction === 'source_to_target' ? 'url(#arrowhead)' : null)
      .attr('class', 'relationship-link')
      .on('mouseover', function(event, d) {
        // Highlight link on hover
        d3.select(this)
          .attr('stroke-width', Math.max(2, Math.min(6, (d.strength || 5) / 1.5)))
          .attr('stroke-opacity', 0.9);
      })
      .on('mouseout', function(event, d) {
        // Restore link on mouseout
        d3.select(this)
          .attr('stroke-width', Math.max(1, Math.min(5, (d.strength || 5) / 2)))
          .attr('stroke-opacity', 0.3 + ((d.strength || 5) / 10) * 0.5);
      });

    // Create arrowhead marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#6B7280')
      .style('stroke', 'none');

    // Create nodes
    const node = nodeGroup
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.color)
      .attr('stroke', d => d.strokeColor)
      .attr('stroke-width', d => d.strokeWidth)
      .attr('class', d => `node ${selectedNodeId === d.id ? 'selected' : ''}`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        if (onNodeClick) onNodeClick(d);
      })
      .on('mouseover', function(event, d) {
        // Highlight connected nodes and links
        const connectedNodeIds = new Set();
        link.style('opacity', l => {
          if (l.source.id === d.id || l.target.id === d.id) {
            connectedNodeIds.add(l.source.id);
            connectedNodeIds.add(l.target.id);
            return 1;
          }
          return 0.2;
        });
        
        node.style('opacity', n => connectedNodeIds.has(n.id) || n.id === d.id ? 1 : 0.3);
        
        // Show tooltip
        showTooltip(event, d);
      })
      .on('mouseout', function() {
        link.style('opacity', 0.6);
        node.style('opacity', 1);
        hideTooltip();
      });

    // Add node labels
    const labels = nodeGroup
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text(d => d.name)
      .attr('font-size', '12px')
      .attr('font-family', 'system-ui, sans-serif')
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.radius + 15)
      .attr('fill', '#374151')
      .style('pointer-events', 'none')
      .style('user-select', 'none');

    // Add drag behavior
    const drag = d3.drag()
      .on('start', (event, d) => {
        if (!event.active) newSimulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) newSimulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(drag);

    // Update positions on tick
    newSimulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      labels
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });

    setSimulation(newSimulation);

    return () => {
      if (newSimulation) {
        newSimulation.stop();
      }
    };
  }, [stakeholders, relationships, dimensions, selectedNodeId]);

  // Tooltip functions
  const showTooltip = (event, d) => {
    const tooltip = d3.select('body').append('div')
      .attr('class', 'stakeholder-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', 'white')
      .style('padding', '12px')
      .style('border-radius', '8px')
      .style('font-size', '14px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('opacity', 0);

    tooltip.html(`
      <div style="font-weight: bold; margin-bottom: 8px;">${d.name}</div>
      <div style="margin-bottom: 4px;"><strong>Role:</strong> ${d.role}</div>
      <div style="margin-bottom: 4px;"><strong>Company:</strong> ${d.company}</div>
      <div style="margin-bottom: 4px;"><strong>Influence:</strong> ${d.influence}/10</div>
      <div style="margin-bottom: 4px;"><strong>Interest:</strong> ${d.interest}/10</div>
      <div style="margin-bottom: 4px;"><strong>Sentiment:</strong> ${d.sentiment}</div>
      <div style="margin-bottom: 4px;"><strong>Trust:</strong> ${d.trust_level}/10</div>
      ${d.email ? `<div style="margin-bottom: 4px;"><strong>Email:</strong> ${d.email}</div>` : ''}
      ${d.phone ? `<div><strong>Phone:</strong> ${d.phone}</div>` : ''}
    `)
    .style('left', (event.pageX + 10) + 'px')
    .style('top', (event.pageY - 10) + 'px')
    .transition()
    .duration(200)
    .style('opacity', 1);
  };

  const hideTooltip = () => {
    d3.selectAll('.stakeholder-tooltip').remove();
  };

  // Zoom functions
  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom().scaleExtent([0.1, 4]);
    svg.transition().call(zoom.scaleBy, 1.5);
  };

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom().scaleExtent([0.1, 4]);
    svg.transition().call(zoom.scaleBy, 1 / 1.5);
  };

  const handleResetView = () => {
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom().scaleExtent([0.1, 4]);
    svg.transition().call(zoom.transform, d3.zoomIdentity);
  };

  // Set up zoom behavior
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const container = svg.select('.network-container');

    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
        setTransform(event.transform);
      });

    svg.call(zoom);

    return () => {
      svg.on('.zoom', null);
    };
  }, []);

  // Handle container resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.max(400, rect.height)
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Re-run visualization when filters change
  useEffect(() => {
    // This will trigger the main visualization useEffect
  }, [selectedFilters]);

  // Get unique values for filters
  const getUniqueCompanies = () => {
    const companies = [...new Set(stakeholders.map(s => s.company).filter(Boolean))];
    return companies.sort();
  };

  const getNetworkStats = () => {
    const totalNodes = stakeholders.length;
    const totalLinks = relationships.filter(r => r.is_active !== false).length;
    const avgInfluence = stakeholders.reduce((sum, s) => sum + (s.influence || 5), 0) / totalNodes;
    const sentimentCounts = stakeholders.reduce((acc, s) => {
      acc[s.sentiment || 'neutral'] = (acc[s.sentiment || 'neutral'] || 0) + 1;
      return acc;
    }, {});

    return {
      totalNodes,
      totalLinks,
      avgInfluence: avgInfluence.toFixed(1),
      sentimentCounts
    };
  };

  const stats = getNetworkStats();

  return (
    <div className={`stakeholder-network-map ${className}`}>
      {/* Header with stats and controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-blue-600" />
            <span className="font-semibold">Stakeholder Network</span>
          </div>
          <div className="flex gap-4 text-sm text-gray-600">
            <Badge variant="outline" className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {stats.totalNodes} nodes
            </Badge>
            <Badge variant="outline">
              {stats.totalLinks} connections
            </Badge>
            <Badge variant="outline">
              Avg. Influence: {stats.avgInfluence}
            </Badge>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={handleZoomIn}>
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom In</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={handleZoomOut}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Zoom Out</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={handleResetView}>
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Reset View</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Filters Panel */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filters
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedFilters({
                sentiment: 'all',
                influence: 'all',
                company: 'all',
                role: 'all',
                strategic_value: 'all',
                trust_level: 'all',
                relationship_type: 'all'
              })}
              className="h-6 text-xs"
            >
              Clear All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {/* Company Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Company</Label>
              <Select
                value={selectedFilters.company}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, company: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Companies</SelectItem>
                  {getUniqueCompanies().map(company => (
                    <SelectItem key={company} value={company}>{company}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Role Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Role</Label>
              <Select
                value={selectedFilters.role}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, role: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  {[...new Set(stakeholders.map(s => s.role).filter(Boolean))].sort().map(role => (
                    <SelectItem key={role} value={role}>{role}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sentiment Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Sentiment</Label>
              <Select
                value={selectedFilters.sentiment}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, sentiment: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="positive">Positive</SelectItem>
                  <SelectItem value="neutral">Neutral</SelectItem>
                  <SelectItem value="negative">Negative</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Influence Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Influence</Label>
              <Select
                value={selectedFilters.influence}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, influence: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="1">Low (1-2)</SelectItem>
                  <SelectItem value="2">Medium (3-5)</SelectItem>
                  <SelectItem value="3">High (6-7)</SelectItem>
                  <SelectItem value="4">Very High (8-10)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Strategic Value Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Strategic Value</Label>
              <Select
                value={selectedFilters.strategic_value}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, strategic_value: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Trust Level Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Trust Level</Label>
              <Select
                value={selectedFilters.trust_level}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, trust_level: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="1">Low (1-2)</SelectItem>
                  <SelectItem value="2">Medium (3-5)</SelectItem>
                  <SelectItem value="3">High (6-7)</SelectItem>
                  <SelectItem value="4">Very High (8-10)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Relationship Type Filter */}
            <div className="space-y-1">
              <Label className="text-xs">Relationship</Label>
              <Select
                value={selectedFilters.relationship_type}
                onValueChange={(value) => setSelectedFilters({ ...selectedFilters, relationship_type: value })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {[...new Set(relationships.map(r => r.relationship_type).filter(Boolean))].sort().map(type => (
                    <SelectItem key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <h4 className="font-medium mb-2">Sentiment</h4>
            <div className="flex gap-3">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span>Positive</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                <span>Neutral</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>Negative</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-medium mb-2">Influence (Border)</h4>
            <div className="flex gap-3">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-gray-300 border-2 border-red-600"></div>
                <span>High (8-10)</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-gray-300 border-2 border-amber-500"></div>
                <span>Medium (6-7)</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-gray-300 border border-gray-500"></div>
                <span>Low (1-5)</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-medium mb-2">Node Size</h4>
            <div className="flex items-center gap-1">
              <span>Represents influence level</span>
            </div>
          </div>
        </div>
      </div>

      {/* Network visualization */}
      <Card>
        <CardContent className="p-0">
          <div ref={containerRef} className="w-full h-[600px] relative overflow-hidden">
            <svg
              ref={svgRef}
              width={dimensions.width}
              height={dimensions.height}
              className="border rounded-lg"
            >
              <g className="network-container"></g>
            </svg>
            
            {stakeholders.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No stakeholders to display</p>
                  <p className="text-sm">Add stakeholders to see the network visualization</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Network insights */}
      {stakeholders.length > 0 && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Sentiment Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(stats.sentimentCounts).map(([sentiment, count]) => (
                  <div key={sentiment} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: getSentimentColor(sentiment) }}
                      ></div>
                      <span className="capitalize text-sm">{sentiment}</span>
                    </div>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Network Density</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {((stats.totalLinks / Math.max(1, stats.totalNodes * (stats.totalNodes - 1) / 2)) * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Percentage of possible connections that exist
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Key Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                <p>• {stats.totalNodes} stakeholders mapped</p>
                <p>• {stats.totalLinks} relationships tracked</p>
                <p>• Average influence: {stats.avgInfluence}/10</p>
                <p>• Most common: {Object.entries(stats.sentimentCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A'} sentiment</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default StakeholderNetworkMap;
