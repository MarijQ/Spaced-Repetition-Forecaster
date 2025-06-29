export interface Note {
  id: number;
  parent_id: number | null;
  title: string;
  content: string;
}
