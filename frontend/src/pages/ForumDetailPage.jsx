import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function ForumDetailPage() {
  const { id }       = useParams();
  const { user }     = useAuth();
  const forumId      = parseInt(id);

  const [threads,    setThreads]    = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [activeThread, setActiveThread] = useState(null);
  const [replies,    setReplies]    = useState([]);
  const [msg,        setMsg]        = useState("");

  const [newThread,  setNewThread]  = useState({ thread_title: "", starting_post: "" });
  const [replyText,  setReplyText]  = useState("");
  const [replyTo,    setReplyTo]    = useState(null); // reply_id for nested

  useEffect(() => {
    api.getThreads(forumId).then((t) => { setThreads(t); setLoading(false); });
  }, [forumId]);

  const loadReplies = async (threadId) => {
    setActiveThread(threadId);
    const r = await api.getReplies(threadId);
    setReplies(r);
    setReplyTo(null);
    setReplyText("");
  };

  const handleCreateThread = async (e) => {
    e.preventDefault();
    try {
      await api.createThread(forumId, newThread);
      const t = await api.getThreads(forumId);
      setThreads(t);
      setNewThread({ thread_title: "", starting_post: "" });
      setMsg("Thread created.");
    } catch (err) { setMsg(err.message); }
  };

  const handleReply = async (e) => {
    e.preventDefault();
    try {
      await api.createReply(activeThread, {
        reply_text:      replyText,
        parent_reply_id: replyTo,
      });
      const r = await api.getReplies(activeThread);
      setReplies(r);
      setReplyText("");
      setReplyTo(null);
    } catch (err) { setMsg(err.message); }
  };

  // Build nested reply tree
  const buildTree = (replies) => {
    const map = {};
    const roots = [];
    replies.forEach((r) => (map[r.reply_id] = { ...r, children: [] }));
    replies.forEach((r) => {
      if (r.parent_reply_id && map[r.parent_reply_id]) {
        map[r.parent_reply_id].children.push(map[r.reply_id]);
      } else {
        roots.push(map[r.reply_id]);
      }
    });
    return roots;
  };

  const ReplyNode = ({ reply, depth = 0 }) => (
    <div className="reply-node" style={{ marginLeft: depth * 24 }}>
      <div className="reply-meta">
        <strong>{reply.first_name} {reply.last_name}</strong>
        <span className="muted">{reply.created_at?.slice(0, 10)}</span>
      </div>
      <p className="reply-text">{reply.reply_text}</p>
      <button className="btn-link" onClick={() => setReplyTo(reply.reply_id)}>
        Reply
      </button>
      {reply.children.map((c) => (
        <ReplyNode key={c.reply_id} reply={c} depth={depth + 1} />
      ))}
    </div>
  );

  if (loading) return <div className="loading">Loading forum...</div>;

  const activeThreadObj = threads.find((t) => t.thread_id === activeThread);

  return (
    <div className="page">
      <div className="page-header">
        <button className="back-link" onClick={() => activeThread ? setActiveThread(null) : null}>
          {activeThread ? "← Back to Threads" : "Forum"}
        </button>
        <h1>{activeThread ? activeThreadObj?.thread_title : "Discussion Forum"}</h1>
      </div>

      {msg && <div className="alert alert-info">{msg}</div>}

      {/* Thread list */}
      {!activeThread && (
        <>
          <div className="card mb-4">
            <h3>Start a New Thread</h3>
            <form onSubmit={handleCreateThread}>
              <div className="form-group">
                <label>Title</label>
                <input value={newThread.thread_title}
                  onChange={(e) => setNewThread({ ...newThread, thread_title: e.target.value })}
                  required />
              </div>
              <div className="form-group">
                <label>Post</label>
                <textarea value={newThread.starting_post} rows={3}
                  onChange={(e) => setNewThread({ ...newThread, starting_post: e.target.value })}
                  required />
              </div>
              <button type="submit" className="btn btn-primary btn-sm">Post Thread</button>
            </form>
          </div>

          {threads.length === 0 ? (
            <div className="empty-state">No threads yet. Start the discussion!</div>
          ) : (
            threads.map((t) => (
              <div key={t.thread_id} className="thread-row" onClick={() => loadReplies(t.thread_id)}>
                <div className="thread-title">{t.thread_title}</div>
                <div className="thread-meta muted">
                  {t.first_name} {t.last_name} · {t.created_at?.slice(0, 10)}
                </div>
                <p className="thread-preview">{t.starting_post?.slice(0, 120)}...</p>
              </div>
            ))
          )}
        </>
      )}

      {/* Thread detail + replies */}
      {activeThread && activeThreadObj && (
        <>
          <div className="card mb-4">
            <div className="reply-meta">
              <strong>{activeThreadObj.first_name} {activeThreadObj.last_name}</strong>
              <span className="muted">{activeThreadObj.created_at?.slice(0, 10)}</span>
            </div>
            <p>{activeThreadObj.starting_post}</p>
          </div>

          <h3>Replies ({replies.length})</h3>
          <div className="reply-tree">
            {buildTree(replies).map((r) => (
              <ReplyNode key={r.reply_id} reply={r} />
            ))}
          </div>

          <div className="card mt-4">
            <h4>{replyTo ? `Replying to reply #${replyTo}` : "Add a Reply"}</h4>
            {replyTo && (
              <button className="btn-link mb-1" onClick={() => setReplyTo(null)}>
                Cancel nested reply
              </button>
            )}
            <form onSubmit={handleReply}>
              <textarea value={replyText} rows={3} placeholder="Write your reply..."
                onChange={(e) => setReplyText(e.target.value)} required />
              <button type="submit" className="btn btn-primary btn-sm mt-1">Post Reply</button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
