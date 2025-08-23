import React from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

interface TableNodeData {
  label: string;
  group: string;
  fullName: string;
  groupColor: string;
  isInLineage?: boolean;
  isSelected?: boolean;
  isFaded?: boolean;
}

const TableNode: React.FC<NodeProps<TableNodeData>> = ({ data }) => {
  const nodeClasses = [
    'table-node',
    data.isSelected ? 'selected-table' : '',
    data.isInLineage ? 'lineage-table' : '',
    data.isFaded ? 'faded-table' : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={nodeClasses}>
      <Handle type="target" position={Position.Left} />
      
      <div className="table-node-content" style={{ background: data.groupColor }}>
        <div className="table-name">{data.label}</div>
      </div>
      
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default TableNode;
