export type GroupedGraphJSON = Array<{
  group: string;
  tables: Array<{
    name: string;
    dependencies: string[]; // "group.table"
  }>;
}>;

export type TableId = string;
