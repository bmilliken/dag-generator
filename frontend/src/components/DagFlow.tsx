import React, { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  MarkerType,
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import TableNode from './TableNode';
import TableDetailsPanel from './TableDetailsPanel';
import './DagFlow.css';

const nodeTypes = {
  tableNode: TableNode,
};

interface DagData {
  groups: {
    group: string;
    tables: string[];
  }[];
  connections: {
    from: string;
    to: string;
  }[];
}

interface ProjectInfo {
  current_project: string;
  available_projects: string[];
  initialized: boolean;
  has_pending_changes?: boolean;
  pending_changes_count?: number;
}

interface TableDetails {
  target_table: string;
  columns_lineage: Array<{
    column: {
      full_path: string;
      description: string;
      is_source_column: boolean;
      immediate_dependencies?: Array<{
        full_path: string;
        description: string;
      }>;
      source_columns?: Array<{
        full_path: string;
        description: string;
      }>;
    };
  }>;
  groups: Array<{
    group: string;
    tables: string[];
  }>;
  connections: Array<{
    from: string;
    to: string;
  }>;
}

const DagFlow: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<TableDetails | null>(null);
  const [showDetailsPanel, setShowDetailsPanel] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const API_BASE = 'http://localhost:5002';

  // Color assignment cache to ensure consistency
  const [colorAssignments, setColorAssignments] = useState<{ [key: string]: string }>({});

  // Convert hex to RGB for distance calculation
  const hexToRgb = useCallback((hex: string): [number, number, number] => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
    ] : [0, 0, 0];
  }, []);

  // Calculate color distance using Delta E (simplified)
  const colorDistance = useCallback((color1: string, color2: string): number => {
    const [r1, g1, b1] = hexToRgb(color1);
    const [r2, g2, b2] = hexToRgb(color2);
    
    // Simple Euclidean distance in RGB space (weighted for human perception)
    const deltaR = (r1 - r2) * 0.3;
    const deltaG = (g1 - g2) * 0.59;
    const deltaB = (b1 - b2) * 0.11;
    
    return Math.sqrt(deltaR * deltaR + deltaG * deltaG + deltaB * deltaB);
  }, [hexToRgb]);

  // Convert HSB to hex color
  const hsbToHex = useCallback((h: number, s: number, b: number): string => {
    // Normalize values
    h = h % 360;
    s = Math.max(0, Math.min(100, s)) / 100;
    b = Math.max(0, Math.min(100, b)) / 100;
    
    const c = b * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = b - c;
    
    let r = 0, g = 0, bl = 0;
    
    if (h >= 0 && h < 60) {
      r = c; g = x; bl = 0;
    } else if (h >= 60 && h < 120) {
      r = x; g = c; bl = 0;
    } else if (h >= 120 && h < 180) {
      r = 0; g = c; bl = x;
    } else if (h >= 180 && h < 240) {
      r = 0; g = x; bl = c;
    } else if (h >= 240 && h < 300) {
      r = x; g = 0; bl = c;
    } else if (h >= 300 && h < 360) {
      r = c; g = 0; bl = x;
    }
    
    r = Math.round((r + m) * 255);
    g = Math.round((g + m) * 255);
    bl = Math.round((bl + m) * 255);
    
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${bl.toString(16).padStart(2, '0')}`;
  }, []);

  // Generate colors using HSB with only hue as variable
  const generateDistinctColors = useCallback((count: number): string[] => {
    if (count === 0) return [];
    
    const colors: string[] = [];
    const saturation = 100; // Max saturation for maximum vibrancy
    const brightness = 75; // Lowered brightness for darker colors
    
    // Divide hue range by (groups + 1) to avoid going full circle
    const hueStep = 360 / (count + 1);
    
    for (let i = 0; i < count; i++) {
      // Start from hue 0 and add group number * step
      const hue = i * hueStep;
      const color = hsbToHex(hue, saturation, brightness);
      colors.push(color);
    }
    
    return colors;
  }, [hsbToHex]);

  // Memoize the group color function with HSB-based color generation
  const getGroupColor = useCallback((groupName: string): string => {
    // If color already assigned, return it
    if (colorAssignments[groupName]) {
      return colorAssignments[groupName];
    }

    // Get all unique groups from current nodes to determine total count
    const allGroups = nodes.length > 0 
      ? Array.from(new Set(nodes.map(node => node.data.group))).sort()
      : [];
    
    // Return empty string if no groups available
    if (allGroups.length === 0) {
      return '';
    }

    // Generate colors for all groups at once using HSB
    const totalGroups = allGroups.length;
    const selectedColors = generateDistinctColors(totalGroups);
    
    // Assign colors to all groups in a deterministic way
    const newAssignments: { [key: string]: string } = {};
    allGroups.forEach((group, index) => {
      if (colorAssignments[group]) {
        // Keep existing assignment
        newAssignments[group] = colorAssignments[group];
      } else {
        // Assign new color from HSB generation
        newAssignments[group] = selectedColors[index % selectedColors.length];
      }
    });
    
    // Update all assignments at once
    setColorAssignments(prev => ({ ...prev, ...newAssignments }));
    
    return newAssignments[groupName] || selectedColors[0];
  }, [nodes, colorAssignments, generateDistinctColors]);

  // Refresh project data
  const refreshProject = async () => {
    if (!projectInfo?.current_project) return;
    
    setRefreshing(true);
    setError(null);
    
    try {
      // Call refresh endpoint
      const refreshResponse = await axios.post(`${API_BASE}/refresh`);
      console.log('Refresh response:', refreshResponse.data);
      
      // Fetch updated project info
      await fetchProjectInfo();
      
      // Fetch updated DAG data
      await fetchDagData();
      
    } catch (err) {
      console.error('Failed to refresh project:', err);
      setError('Failed to refresh project data');
    } finally {
      setRefreshing(false);
    }
  };

  // Fetch project info
  const fetchProjectInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE}/project`);
      console.log('Project info received:', response.data); // Debug log
      setProjectInfo(response.data);
    } catch (err) {
      console.error('Failed to fetch project info:', err);
      setError('Failed to fetch project information');
    }
  };

  // Fetch DAG data from the API
  const fetchDagData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE}/dag`);
      const dagData: DagData = response.data;
      
      // Convert DAG data to React Flow format
      const { nodes: convertedNodes, edges: convertedEdges } = convertDagToFlow(dagData);
      
      setNodes(convertedNodes);
      setEdges(convertedEdges);
    } catch (err) {
      console.error('Failed to fetch DAG data:', err);
      setError('Failed to load DAG data. Make sure the backend server is running on port 5002.');
    } finally {
      setLoading(false);
    }
  };

  // Convert DAG data to React Flow nodes and edges
  const convertDagToFlow = (dagData: DagData) => {
    console.log('Converting DAG data to React Flow:', dagData);
    
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    
    // Pre-assign colors for all groups before creating nodes
    const allGroups = Array.from(new Set(dagData.groups.map(group => group.group))).sort();
    const selectedColors = generateDistinctColors(allGroups.length);
    const groupColors: { [key: string]: string } = {};
    
    allGroups.forEach((group, index) => {
      groupColors[group] = selectedColors[index % selectedColors.length];
    });
    
    // Build a map of table names to their full names for easier lookups
    const tableMap: { [tableName: string]: string } = {};
    dagData.groups.forEach((group) => {
      group.tables.forEach((tableName) => {
        const fullName = `${group.group}.${tableName}`;
        tableMap[tableName] = fullName;
      });
    });
    
    // Build dependency graph to determine hierarchical levels
    const dependents: { [key: string]: string[] } = {}; // what depends on this table
    const dependencies: { [key: string]: string[] } = {}; // what this table depends on
    
    // Initialize dependency tracking for all tables
    dagData.groups.forEach((group) => {
      group.tables.forEach((tableName) => {
        const fullName = `${group.group}.${tableName}`;
        dependents[fullName] = [];
        dependencies[fullName] = [];
      });
    });
    
    // Process connections to build dependency graph
    dagData.connections.forEach((connection) => {
      const fromTable = connection.from;
      const toTable = connection.to;
      
      if (dependents[fromTable] && dependencies[toTable]) {
        dependents[fromTable].push(toTable);
        dependencies[toTable].push(fromTable);
      }
    });
    
    // Calculate dependency levels (0 = no dependencies, 1 = depends on level 0, etc.)
    const levels: { [key: string]: number } = {};
    const visited = new Set<string>();
    
    const calculateLevel = (tableName: string): number => {
      if (visited.has(tableName)) {
        return levels[tableName] || 0; // Prevent infinite recursion
      }
      
      visited.add(tableName);
      
      const deps = dependencies[tableName] || [];
      if (deps.length === 0) {
        levels[tableName] = 0; // No dependencies = level 0 (leftmost)
        return 0;
      }
      
      // Level is 1 + max level of dependencies
      const maxDepLevel = Math.max(...deps.map(dep => calculateLevel(dep)));
      levels[tableName] = maxDepLevel + 1;
      return levels[tableName];
    };
    
    // Calculate levels for all tables
    dagData.groups.forEach((group) => {
      group.tables.forEach((tableName) => {
        const fullName = `${group.group}.${tableName}`;
        calculateLevel(fullName);
      });
    });
    
    // Group tables by level and group for positioning
    const levelGroups: { [level: number]: { [group: string]: string[] } } = {};
    dagData.groups.forEach((group) => {
      group.tables.forEach((tableName) => {
        const fullName = `${group.group}.${tableName}`;
        const level = levels[fullName];
        
        if (!levelGroups[level]) {
          levelGroups[level] = {};
        }
        if (!levelGroups[level][group.group]) {
          levelGroups[level][group.group] = [];
        }
        levelGroups[level][group.group].push(tableName);
      });
    });
    
    // Position nodes based on levels (left-to-right) and groups (top-to-bottom)
    const levelWidth = 450; // Increased horizontal spacing between dependency levels
    const groupHeight = 180; // Increased vertical spacing between groups
    const tableHeight = 120; // Increased vertical spacing between tables in same group
    
    Object.keys(levelGroups).sort((a, b) => parseInt(a) - parseInt(b)).forEach((levelStr) => {
      const level = parseInt(levelStr);
      const groupsInLevel = levelGroups[level];
      let groupIndex = 0;
      
      Object.keys(groupsInLevel).forEach((groupName) => {
        const tablesInGroup = groupsInLevel[groupName];
        const groupColor = groupColors[groupName]; // Use pre-assigned color
        
        tablesInGroup.forEach((tableName, tableIndex) => {
          const fullName = `${groupName}.${tableName}`;
          
          nodes.push({
            id: fullName,
            type: 'tableNode',
            data: {
              label: tableName,
              group: groupName,
              fullName: fullName,
              groupColor: groupColor,
            },
            position: {
              x: level * levelWidth + 50, // Left to right based on dependency level
              y: groupIndex * groupHeight + tableIndex * tableHeight + 50,
            },
          });
        });
        
        groupIndex++;
      });
    });
    
    // Create edges for connections with curved bezier lines
    dagData.connections.forEach((connection, index) => {
      edges.push({
        id: `edge-${index}`,
        source: connection.from,
        target: connection.to,
        type: 'default', // Use default bezier curves instead of smoothstep
        animated: false, // Static by default, animated via CSS classes
        style: {
          stroke: '#64748b',
          strokeWidth: 3,
          opacity: 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#64748b',
        },
      });
    });
    
    // Update color assignments cache
    setColorAssignments(groupColors);
    
    return { nodes, edges };
  };

  // Optimized function to update node styles without causing re-renders during drag
  const updateNodeStyles = useCallback((lineageData: any, selectedTable: string) => {
    setNodes(currentNodes => 
      currentNodes.map(node => {
        const [groupName, tableNameFromNode] = node.id.split('.');
        const isInLineage = lineageData.groups.some((group: any) => 
          group.group === groupName && group.tables.includes(tableNameFromNode)
        );
        const isSelected = selectedTable === tableNameFromNode;
        
        // Only update if className would actually change
        let newClassName = 'table-node';
        if (isSelected) {
          newClassName += ' selected-table';
        } else if (isInLineage) {
          newClassName += ' lineage-table';
        } else {
          newClassName += ' faded-table';
        }
        
        // Avoid unnecessary re-renders by checking if className actually changed
        if (node.className === newClassName) {
          return node;
        }
        
        return {
          ...node,
          className: newClassName,
        };
      })
    );
  }, [setNodes]);

  // Optimized function to update edge styles
  const updateEdgeStyles = useCallback((lineageData: any) => {
    setEdges(currentEdges => 
      currentEdges.map(edge => {
        const isLineageEdge = lineageData.connections.some((lineageConn: any) => 
          lineageConn.from === edge.source && lineageConn.to === edge.target
        );
        
        const newClassName = isLineageEdge ? 'lineage-edge' : 'faded-edge';
        const newStyle = {
          stroke: isLineageEdge ? '#3b82f6' : '#94a3b8',
          strokeWidth: isLineageEdge ? 4 : 2,
          opacity: isLineageEdge ? 1 : 0.3,
        };
        
        // Avoid unnecessary re-renders by checking if styles actually changed
        if (edge.className === newClassName && 
            edge.style?.stroke === newStyle.stroke &&
            edge.style?.strokeWidth === newStyle.strokeWidth &&
            edge.style?.opacity === newStyle.opacity) {
          return edge;
        }
        
        return {
          ...edge,
          className: newClassName,
          style: newStyle,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isLineageEdge ? '#3b82f6' : '#94a3b8',
          }
        };
      })
    );
  }, [setEdges]);

  // Fetch lineage data for a specific table (optimized)
  const fetchLineage = useCallback(async (tableName: string) => {
    try {
      const response = await axios.get(`${API_BASE}/table/${tableName}/lineage`);
      const lineageData = response.data;
      setSelectedTable(tableName);
      setTableDetails(lineageData);
      // Only show details panel if sidebar is visible
      setShowDetailsPanel(sidebarVisible);
      console.log('Lineage data:', lineageData);
      console.log('Selected table:', tableName);
      
      // Use optimized update functions
      updateNodeStyles(lineageData, tableName);
      updateEdgeStyles(lineageData);
      
    } catch (err) {
      console.error('Failed to fetch lineage:', err);
    }
  }, [API_BASE, updateNodeStyles, updateEdgeStyles, sidebarVisible]);

  // Clear lineage selection (optimized)
  const clearLineage = useCallback(() => {
    setSelectedTable(null);
    setTableDetails(null);
    setShowDetailsPanel(false);
    
    // Reset all nodes to normal styling (optimized)
    setNodes(currentNodes => 
      currentNodes.map(node => {
        if (node.className === 'table-node') {
          return node; // No change needed
        }
        return {
          ...node,
          className: 'table-node',
        };
      })
    );
    
    // Reset all edges to normal styling (optimized)
    setEdges(currentEdges => 
      currentEdges.map(edge => {
        const newStyle = {
          stroke: '#64748b',
          strokeWidth: 3,
          opacity: 1,
        };
        
        if (!edge.className && 
            edge.style?.stroke === newStyle.stroke &&
            edge.style?.strokeWidth === newStyle.strokeWidth &&
            edge.style?.opacity === newStyle.opacity) {
          return edge; // No change needed
        }
        
        return {
          ...edge,
          className: '',
          style: newStyle,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#64748b',
          }
        };
      })
    );
  }, [setNodes, setEdges]);

  // Handle node click (optimized)
  const onNodeClick = useCallback((_event: React.MouseEvent, node: any) => {
    if (selectedTable === node.data.label) {
      // If clicking the same table, clear selection
      clearLineage();
    } else {
      // Extract just the table name from the full path (e.g., "src.customers" -> "customers")
      const tableName = node.data.label;
      fetchLineage(tableName);
    }
  }, [selectedTable, clearLineage, fetchLineage]);

  // Handle connection creation
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Switch project
  const switchProject = async (projectName: string) => {
    if (!projectName || projectName === projectInfo?.current_project) return;
    
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/project/${projectName}`);
      await fetchProjectInfo(); // This should update projectInfo with new current_project
      await fetchDagData();
      console.log('Project switched to:', projectName); // Debug log
    } catch (err) {
      console.error('Failed to switch project:', err);
      setError(`Failed to switch to project: ${projectName}`);
      setLoading(false);
    }
  };

  // Toggle sidebar visibility
  const toggleSidebar = useCallback(() => {
    setSidebarVisible(prev => {
      const newVisibility = !prev;
      // If hiding sidebar, also hide details panel
      if (!newVisibility) {
        setShowDetailsPanel(false);
      } else if (selectedTable && tableDetails) {
        // If showing sidebar and there's a selected table, show details panel
        setShowDetailsPanel(true);
      }
      return newVisibility;
    });
  }, [selectedTable, tableDetails]);

  // Initialize colors when nodes are loaded or groups change
  useEffect(() => {
    if (nodes.length > 0) {
      const uniqueGroups = Array.from(new Set(nodes.map(node => node.data.group)));
      const currentGroups = Object.keys(colorAssignments);
      
      // Check if we have new groups that need colors
      const newGroups = uniqueGroups.filter(group => !currentGroups.includes(group));
      
      if (newGroups.length > 0) {
        // Use HSB-based color generation for all groups
        const totalGroups = uniqueGroups.length;
        const selectedColors = generateDistinctColors(totalGroups);
        
        // Create new assignments, preserving existing ones
        const newAssignments: { [key: string]: string } = { ...colorAssignments };
        
        // Assign colors to groups that don't have them yet
        let colorIndex = 0;
        uniqueGroups.forEach(group => {
          if (!newAssignments[group]) {
            newAssignments[group] = selectedColors[colorIndex % selectedColors.length];
            colorIndex++;
          }
        });
        
        setColorAssignments(newAssignments);
      }
    }
  }, [nodes, generateDistinctColors, colorAssignments]);

  // Handle escape key to clear selection
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && selectedTable) {
        clearLineage();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedTable, clearLineage]);

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      await fetchProjectInfo();
      await fetchDagData();
    };
    
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="dag-loading">
        <div className="spinner"></div>
        <p>Loading DAG data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dag-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={fetchDagData} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dag-container">
      <div className="dag-header">
        <div className="project-selector">
          <label htmlFor="project-select">Project: </label>
          <select
            id="project-select"
            value={projectInfo?.current_project || ''}
            onChange={(e) => switchProject(e.target.value)}
            disabled={!projectInfo}
          >
            {!projectInfo && (
              <option value="">Loading...</option>
            )}
            {projectInfo?.available_projects?.map((project) => (
              <option key={project} value={project}>
                {project}
              </option>
            ))}
          </select>
        </div>
        
        <div className="dag-controls">
          {projectInfo?.has_pending_changes && (
            <span className="pending-changes">
              📄 {projectInfo.pending_changes_count} file(s) changed
            </span>
          )}
          <button 
            onClick={toggleSidebar}
            className="toggle-sidebar-button"
            title={sidebarVisible ? 'Hide sidebar' : 'Show sidebar'}
          >
            Toggle Sidebar
          </button>
          <button 
            onClick={refreshProject} 
            disabled={refreshing || !projectInfo?.current_project}
            className="refresh-button"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="dag-flow-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="top-right"
          className="dag-flow"
          minZoom={0}
          maxZoom={Infinity}
        >
          <MiniMap />
          <Controls />
          <Background color="#ffffff" />
        </ReactFlow>

        {/* Color Legend */}
        {nodes.length > 0 && (
          <div className="color-legend">
            <h4>Groups</h4>
            {Array.from(new Set(nodes.map(node => node.data.group))).map(group => (
              <div key={group} className="legend-item">
                <div 
                  className="legend-color" 
                  style={{ backgroundColor: getGroupColor(group) }}
                ></div>
                <span title={group}>{group}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Table Details Panel */}
      {showDetailsPanel && tableDetails && sidebarVisible && (
        <TableDetailsPanel
          tableDetails={tableDetails}
          isVisible={showDetailsPanel}
          onClose={clearLineage}
        />
      )}
    </div>
  );
};

export default DagFlow;
