import React, { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  MarkerType,
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import TableNode from './TableNode';
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
}

const DagFlow: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  // Removed lineageData state - we don't need it stored in React state

  const API_BASE = 'http://localhost:5002';

  // Function to generate consistent colors for groups
  const getGroupColor = (groupName: string): string => {
    // Lighter, more readable color palette
    const colors = [
      '#3b82f6', // Blue
      '#10b981', // Emerald
      '#f59e0b', // Amber
      '#ef4444', // Red
      '#8b5cf6', // Violet
      '#06b6d4', // Cyan
      '#84cc16', // Lime
      '#f97316', // Orange
      '#ec4899', // Pink
      '#6366f1', // Indigo
    ];
    
    // Generate hash from group name for consistent color selection
    let hash = 0;
    for (let i = 0; i < groupName.length; i++) {
      const char = groupName.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Use absolute value and modulo to get consistent index
    const colorIndex = Math.abs(hash) % colors.length;
    return colors[colorIndex];
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
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    
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
        const groupColor = getGroupColor(groupName);
        
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
    
    return { nodes, edges };
  };

  // Fetch lineage data for a specific table
  const fetchLineage = async (tableName: string) => {
    try {
      const response = await axios.get(`${API_BASE}/table/${tableName}/lineage`);
      const lineageData = response.data;
      setSelectedTable(tableName);
      console.log('Lineage data:', lineageData);
      console.log('Selected table:', tableName);
      
      // Update node styles using React Flow's state management
      setNodes(currentNodes => 
        currentNodes.map(node => {
          const [groupName, tableNameFromNode] = node.id.split('.');
          const isInLineage = lineageData.groups.some((group: any) => 
            group.group === groupName && group.tables.includes(tableNameFromNode)
          );
          const isSelected = tableName === tableNameFromNode;
          
          // Determine the appropriate class
          let className = 'table-node';
          if (isSelected) {
            className += ' selected-table';
          } else if (isInLineage) {
            className += ' lineage-table';
          } else {
            className += ' faded-table';
          }
          
          return {
            ...node,
            className: className,
          };
        })
      );
      
      // Update edge styles using React Flow's state management
      setEdges(currentEdges => 
        currentEdges.map(edge => {
          const isLineageEdge = lineageData.connections.some((lineageConn: any) => 
            lineageConn.from === edge.source && lineageConn.to === edge.target
          );
          
          return {
            ...edge,
            className: isLineageEdge ? 'lineage-edge' : 'faded-edge',
            style: {
              stroke: isLineageEdge ? '#3b82f6' : '#94a3b8',
              strokeWidth: isLineageEdge ? 4 : 2,
              opacity: isLineageEdge ? 1 : 0.3,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isLineageEdge ? '#3b82f6' : '#94a3b8',
            }
          };
        })
      );
      
    } catch (err) {
      console.error('Failed to fetch lineage:', err);
    }
  };

  // Clear lineage selection
  const clearLineage = () => {
    setSelectedTable(null);
    
    // Reset all nodes to normal styling
    setNodes(currentNodes => 
      currentNodes.map(node => ({
        ...node,
        className: 'table-node',
      }))
    );
    
    // Reset all edges to normal styling
    setEdges(currentEdges => 
      currentEdges.map(edge => ({
        ...edge,
        className: '',
        style: {
          stroke: '#64748b',
          strokeWidth: 3,
          opacity: 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#64748b',
        }
      }))
    );
  };

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: any) => {
    if (selectedTable === node.data.label) {
      // If clicking the same table, clear selection
      clearLineage();
    } else {
      // Extract just the table name from the full path (e.g., "src.customers" -> "customers")
      const tableName = node.data.label;
      fetchLineage(tableName);
    }
  }, [selectedTable]);

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
            value={projectInfo?.current_project || (projectInfo?.available_projects?.[0] || '')}
            onChange={(e) => switchProject(e.target.value)}
            disabled={!projectInfo}
          >
            {!projectInfo && (
              <option value="" disabled>
                Loading projects...
              </option>
            )}
            {projectInfo?.available_projects?.map((project) => (
              <option key={project} value={project}>
                {project}
              </option>
            ))}
          </select>
        </div>
        <div className="dag-stats">
          <span>Nodes: {nodes.length}</span>
          <span>Connections: {edges.length}</span>
          {selectedTable && (
            <span style={{ color: '#3b82f6', fontWeight: 'bold' }}>
              Lineage: {selectedTable}
            </span>
          )}
        </div>
        <div className="header-buttons">
          {selectedTable && (
            <button onClick={clearLineage} className="clear-lineage-button">
              Clear Lineage
            </button>
          )}
          <button onClick={fetchDagData} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>
      
      {/* Color Legend */}
      <div className="color-legend">
        <h4>Groups</h4>
        {nodes.length > 0 && 
          [...new Set(nodes.map(node => node.data.group))]
            .sort()
            .map((group) => {
              const groupColor = getGroupColor(group);
              return (
                <div key={group} className="legend-item">
                  <div 
                    className="legend-color" 
                    style={{ backgroundColor: groupColor }}
                  ></div>
                  <span>{group}</span>
                </div>
              );
            })
        }
      </div>
      
      <div className="dag-flow">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          onNodeClick={onNodeClick} // Add onNodeClick handler
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e0e0e0" />
        </ReactFlow>
      </div>
    </div>
  );
};

export default DagFlow;
