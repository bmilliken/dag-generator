import React from 'react';
import './TableDetailsPanel.css';

interface ColumnLineage {
  column: {
    full_path: string;
    description: string;
    key_type?: string;
    is_source_column: boolean;
    immediate_dependencies?: Array<{
      full_path: string;
      description: string;
      key_type?: string;
    }>;
    source_columns?: Array<{
      full_path: string;
      description: string;
      key_type?: string;
    }>;
  };
}

interface TableDetails {
  target_table: string;
  table_description?: string;
  columns_lineage: ColumnLineage[];
  groups: Array<{
    group: string;
    tables: string[];
  }>;
  connections: Array<{
    from: string;
    to: string;
  }>;
}

interface TableDetailsPanelProps {
  tableDetails: TableDetails | null;
  isVisible: boolean;
  onClose: () => void;
}

const TableDetailsPanel: React.FC<TableDetailsPanelProps> = ({
  tableDetails,
  isVisible,
  onClose,
}) => {
  if (!tableDetails || !isVisible) {
    return null;
  }

  // Extract table name from full path
  const [, tableName] = tableDetails.target_table.split('.');

  return (
    <div className={`details-panel ${isVisible ? 'visible' : ''}`}>
      <div className="panel-header">
        <div className="header-content">
          <h2>{tableName}</h2>
          {tableDetails.table_description && (
            <p className="table-description">{tableDetails.table_description}</p>
          )}
        </div>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      
      <div className="panel-content">
        {tableDetails.columns_lineage.map((columnLineage, index) => {
          const column = columnLineage.column;
          const [, , columnName] = column.full_path.split('.');
          
          return (
            <div key={index} className="column-item">
              <h3>{columnName}</h3>
              {column.description && 
               !column.description.startsWith('Column ') && 
               <p className="description">{column.description}</p>}
              {column.key_type && (
                <span className={`key-tag ${column.key_type}`}>
                  {column.key_type === 'primary' ? 'Primary Key' : 'Foreign Key'}
                </span>
              )}
              
              {column.is_source_column && (
                <div className="source-indicator">Source column</div>
              )}
              
              {!column.is_source_column && (
                <div className="dependencies">
                  {column.immediate_dependencies && column.immediate_dependencies.length > 0 && (
                    <div className="dep-section">
                      <h4>Direct Dependencies:</h4>
                      {column.immediate_dependencies.map((dep, depIndex) => {
                        const [depGroup, depTable, depColumn] = dep.full_path.split('.');
                        return (
                          <div key={depIndex} className="dep-item">
                            <span className="dep-path">{depGroup}.{depTable}.{depColumn}</span>
                            {dep.description && 
                             !dep.description.startsWith('Column ') && 
                             <div className="dep-desc">{dep.description}</div>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  
                  {column.source_columns && column.source_columns.length > 0 && (
                    <div className="source-section">
                      <h4>Source Columns:</h4>
                      {column.source_columns.map((source, sourceIndex) => {
                        const [srcGroup, srcTable, srcColumn] = source.full_path.split('.');
                        return (
                          <div key={sourceIndex} className="source-item">
                            <span className="source-path">{srcGroup}.{srcTable}.{srcColumn}</span>
                            {source.description && 
                             !source.description.startsWith('Column ') && 
                             <div className="source-desc">{source.description}</div>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TableDetailsPanel;
