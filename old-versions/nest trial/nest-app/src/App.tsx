import React, { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Note } from "./types";
import { useDebouncedCallback } from "use-debounce";
import "./App.css";

function App() {
  const [columns, setColumns] = useState<Note[][]>([]);
  const [activeNoteIds, setActiveNoteIds] = useState<(number | null)[]>([]);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [editedContent, setEditedContent] = useState<string>("");
  const [tauriLoaded, setTauriLoaded] = useState(false);

  useEffect(() => {
    if (window.__TAURI__) {
      setTauriLoaded(true);
    } else {
        console.warn("Tauri API not found. Running in browser mode.");
    }
  }, []);

  const fetchTopLevelNotes = useCallback(async () => {
    try {
      const topLevelNotes = await invoke<Note[]>("get_top_level_notes");
      setColumns([topLevelNotes]);
      setActiveNoteIds([null]);
      setSelectedNote(null);
      setEditedContent("");
    } catch (error) {
      console.error("Failed to fetch top-level notes:", error);
    }
  }, []);

  useEffect(() => {
    fetchTopLevelNotes();
  }, [fetchTopLevelNotes]);

  const handleNoteClick = useCallback(async (note: Note, columnIndex: number) => {
    const newActiveNoteIds = [...activeNoteIds.slice(0, columnIndex + 1)];
    newActiveNoteIds[columnIndex] = note.id;

    const newColumns = [...columns.slice(0, columnIndex + 1)];

    setSelectedNote(note);
    setEditedContent(note.content);

    try {
      const childNotes = await invoke<Note[]>("get_child_notes", { parentId: note.id });
      if (childNotes.length > 0) {
        newColumns.push(childNotes);
        newActiveNoteIds.push(null);
      }
      setColumns(newColumns);
      setActiveNoteIds(newActiveNoteIds);
    } catch (error) {
      console.error("Failed to fetch child notes:", error);
    }
  }, [activeNoteIds, columns]);

  const debouncedUpdateNoteContent = useDebouncedCallback(
    async (noteId: number, content: string) => {
      try {
        await invoke("update_note_content", { id: noteId, content });
      } catch (error) {
        console.error("Failed to update note content:", error);
      }
    },
    500
  );

  useEffect(() => {
    if (selectedNote) {
      debouncedUpdateNoteContent(selectedNote.id, editedContent);
    }
  }, [editedContent, selectedNote, debouncedUpdateNoteContent]);

  const handleCreateNote = useCallback(async () => {
    if (!window.__TAURI__) {
      console.error("Tauri API not available. Run the app using 'npm run tauri dev'.");
      alert("This feature is only available in the desktop app.");
      return;
    }

    const title = prompt("Enter note title:");
    if (!title) return;

    const parentId = [...activeNoteIds].reverse().find(id => id !== null) ?? null;

    try {
      await invoke("create_note", { title, parentId });
      // Always refetch from the top to ensure UI consistency.
      await fetchTopLevelNotes();
    } catch (error) {
      console.error("Failed to create note:", error);
      alert(`An error occurred while creating the note: ${error}`);
    }
  }, [activeNoteIds, fetchTopLevelNotes]);


  const handleDeleteNote = useCallback(async () => {
    if (!selectedNote) return;
    if (window.confirm(`Are you sure you want to delete "${selectedNote.title}"?`)) {
      try {
        await invoke("delete_note", { id: selectedNote.id });
        fetchTopLevelNotes();
      } catch (error) {
        console.error("Failed to delete note:", error);
      }
    }
  }, [selectedNote, fetchTopLevelNotes]);

  const handleDrop = useCallback(async (e: React.DragEvent<HTMLDivElement>, newParentId: number | null) => {
    e.preventDefault();
    e.stopPropagation();
    const noteId = parseInt(e.dataTransfer.getData("noteId"));
    if (noteId === newParentId) return;

    try {
      await invoke("update_note_parent", { id: noteId, parentId: newParentId });
      fetchTopLevelNotes();
    } catch (error) {
      console.error("Failed to move note:", error);
    }
  }, [fetchTopLevelNotes]);

  return (
    <div className="app-container">
      <div className="miller-columns-container" onDrop={(e) => handleDrop(e, null)} onDragOver={(e) => e.preventDefault()}>
        {columns.map((column, columnIndex) => (
          <div key={columnIndex} className="column">
            {column.map((note) => (
              <div
                key={note.id}
                className={`note-item ${activeNoteIds[columnIndex] === note.id ? "active" : ""}`}
                onClick={() => handleNoteClick(note, columnIndex)}
                draggable
                onDragStart={(e) => e.dataTransfer.setData("noteId", note.id.toString())}
                onDrop={(e) => handleDrop(e, note.id)}
                onDragOver={(e) => e.preventDefault()}
              >
                {note.title}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="editor-container">
        <div className="button-container">
  <button onClick={handleCreateNote} disabled={!tauriLoaded}>Create Note</button>
          <button onClick={handleDeleteNote} disabled={!selectedNote || !tauriLoaded}>
            Delete Note
          </button>
        </div>
        <textarea
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          placeholder={selectedNote ? "Edit..." : "Select a note to begin."}
          disabled={!selectedNote}
        />
      </div>
    </div>
  );
}

export default App;
