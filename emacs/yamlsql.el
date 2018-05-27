;;; -*- lexical-binding: t -*-

(require 'cl)
(require 'request)
(setq lexical-binding t)

(define-derived-mode yamlsql-mode yaml-mode "YAML-SQL"
  "Major mode for YAML-SQL format"
  :abbrev-table nil :syntax-table nil
  )


;;; Custom Variables

(defconst yamlsql-http-headers
  '(("Content-Type" . "application/json")
    ("User-Agent" . "emacs")))

(setq yamlsql-connection-alist
      '(("localhost"
         (conn-string . "postgresql://ryan@localhost:5432/yamlsql-test")
         (search-path . ("public")))))

(setq yamlsql-program "/Users/ryan/source_code/yamlsql/yamlsql/cli.py")
(setq yamlsql-server-port 15555)

;; Variables that used internally
(defvar yamlsql-server-process
  nil
  "Process object for yamlsql server"
  )

(defvar yamlsql-conn-id
  nil
  "Connection ID to yamlsql server for current buffer.")

(defvar yamlsql-output-buffer
  "*yamlsql-output*")

(defvar yamlsql--dbmeta-alist
  '())

(defvar yamlsql--tables-cache
  nil)


;; Utility functions

(defun yamlsql--output (text)
  (let ((buffer (get-buffer-create yamlsql-output-buffer)))
    (with-current-buffer buffer
      (goto-char (point-max))
      (insert (format "%s\n\n" text)))
    (pop-to-buffer buffer))
  )

(defun yamlsql--http-success (buffer callback)
  (function* (lambda (&key data &allow-other-keys)
               (when callback
                 (with-current-buffer buffer
                   (apply callback
                          (list
                           (assoc-default 'status data)
                           (assoc-default 'data data))))))
  ))

(cl-defun yamlsql--http-error (&rest args &key error-thrown &allow-other-keys)
  (message "yamlsql http error: %S" error-thrown))

(defun yamlsql--http-get (endpoint params &optional callback)
    (request
        (format "http://localhost:%s%s" yamlsql-server-port endpoint)
        :type "GET"
        :headers yamlsql-http-headers
        :params params
        :parser 'json-read
        :success (yamlsql--http-success (current-buffer) callback)
        :error 'yamlsql--http-error
        )
    )

(defun yamlsql--http-post (endpoint params &optional callback)
    (request
        (format "http://localhost:%s%s" yamlsql-server-port endpoint)
        :type "POST"
        :headers yamlsql-http-headers
        :data (json-encode params)
        :parser 'json-read
        :success (yamlsql--http-success (current-buffer) callback)
        :error 'yamlsql--http-error
        )
    )

(defun yamlsql--print-text (status data)
  (yamlsql--output (assoc-default 'text data))
  )

(defmacro yamlsql--check-conn (&rest body)
  (append '(if (not yamlsql-conn-id)
               (message "Please use yamlsql-connect to connect to a DB first."))
          body)
  )

(defun yamlsql--find-table ()
  (let ((initial (eldoc-current-symbol))
        (completion-ignore-case t))
    (completing-read "Tables :"
                     yamlsql--tables-cache
                     nil t initial))
  )

(defun yamlsql--find-connections ()
  (let ((completion-ignore-case t))
    (completing-read "Connections :"
                     (mapcar #'(lambda (c) (car c))
                             yamlsql-connection-alist)
                     nil t))
  )


;;; Start and Connect Server

(defun yamlsql-start-server ()
  (unless yamlsql-server-process
    (setq yamlsql-server-process
      (start-process-shell-command "yamlsql-server" "*yamlsql-server*"
                                  (format "%s runserver --debug --port %d"
                                          yamlsql-program yamlsql-server-port))
      )
    )
  )

(defun yamlsql-connect (conn-name)
  (interactive (list (yamlsql--find-connections)))
  (let* ((conn-props (assoc-default conn-name yamlsql-connection-alist))
         (conn-string (assoc-default 'conn-string conn-props))
         (search-path (assoc-default 'search-path conn-props)))
    (yamlsql-start-server)
    (yamlsql--http-post "/connect"
                        `(("conn_string" . ,conn-string)
                          ("search_path" . ,search-path))
                        'yamlsql--on-connected)
    (message "Connecting to %s..." conn-name))
  )

(defun yamlsql--on-connected (status data)
  (setq-local yamlsql-conn-id (assoc-default 'conn_id data))
  (message "Status: %S Connection: %S" status yamlsql-conn-id)
  (yamlsql--build-tables-cache)
  )

(defun yamlsql--build-tables-cache ()
  (yamlsql--check-conn
   (yamlsql--http-get "/list_tables"
                      `(("conn_id" . ,yamlsql-conn-id))
                      (lambda (status data)
                        (setq-local yamlsql--tables-cache
                                    (append (assoc-default 'tables data) nil))
                        (message "Tables cache has been updated with %d entries."
                                 (length yamlsql--tables-cache)))))
  )



;;; Describe tables and fields

(defun yamlsql-describe-table (table-name)
  (interactive (list (yamlsql--find-table)))
  (yamlsql--check-conn
   (yamlsql--http-get "/describe_table"
                      `(("conn_id" . ,yamlsql-conn-id)
                        ("name" . ,table-name))
                      'yamlsql--print-text)
   )
  )

(defun yamlsql-describe-field (name)
  (interactive (list (read-from-minibuffer "Field:" (eldoc-current-symbol))))
  (yamlsql--check-conn
   (let* ((parts (s-split "\\." name))
         (field (-last-item parts))
         (table (s-join "." (-butlast parts))))
     (yamlsql--http-get "/describe_field"
                        `(("conn_id" . ,yamlsql-conn-id)
                          ("table" . ,table)
                          ("field" . ,field))
                        'yamlsql--print-text))
   )
  )



;;; Convert YAML to SQLs

(defun yamlsql-render-sql ()
  (interactive)
  (let ((content (buffer-string))
        (lineno (line-number-at-pos)))
    (yamlsql--http-post "/render_sql"
                        `(("content" . ,content)
                          ("lineno" . ,lineno))
                        (lambda (status data)
                          (yamlsql--output (assoc-default 'sql data)))
                        ))
  )

(defun yamlsql-run-sql ()
  (interactive)
  (let ((content (buffer-string))
        (lineno (line-number-at-pos)))
    (yamlsql--http-post "/run_sql"
                        `(("conn_id" . ,yamlsql-conn-id)
                          ("content" . ,content)
                          ("lineno" . ,lineno))
                        (lambda (status data)
                          (yamlsql--output (assoc-default 'text data)))
                        ))
  )
