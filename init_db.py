import os
import sys
import json

# Ensure UTF-8 stdout on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pymupdf as fitz  # PyMuPDF
from pathlib import Path
from app.config import Config
from app.database import get_db, execute_write
from app.models import UserModel, DepartmentModel, SemesterModel, SubjectModel, MaterialModel, ChunkModel, BookmarkModel, ChatModel
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService

def create_sample_pdf(filepath, title, subject_code, pages_content):
    """Generates a structured academic PDF with genuine course content using PyMuPDF."""
    doc = fitz.open()
    
    for page_idx, (page_title, sections) in enumerate(pages_content):
        page = doc.new_page(width=595, height=842) # A4 size
        
        # Header banner
        page.draw_rect(fitz.Rect(40, 35, 555, 75), color=(0.4, 0.2, 0.7), fill=(0.15, 0.1, 0.35))
        page.insert_text(fitz.Point(50, 55), f"PADIKA AI — COLLEGE ACADEMIC MATERIALS", fontsize=10, color=(0.8, 0.7, 1.0))
        page.insert_text(fitz.Point(50, 70), f"Subject: {subject_code} | {title}", fontsize=11, color=(1, 1, 1))

        # Page Heading
        page.insert_text(fitz.Point(40, 110), f"Page {page_idx + 1}: {page_title}", fontsize=16, color=(0.2, 0.1, 0.5))
        page.draw_line(fitz.Point(40, 120), fitz.Point(555, 120), color=(0.6, 0.5, 0.8), width=1)

        # Clean flowable academic content box
        full_body = ""
        for sec_heading, sec_body in sections:
            full_body += f"{sec_heading}\n{sec_body.strip()}\n\n"

        text_rect = fitz.Rect(40, 130, 555, 785)
        page.insert_textbox(text_rect, full_body.strip(), fontsize=10, color=(0.15, 0.15, 0.15), lineheight=1.35)

        # Footer
        page.draw_line(fitz.Point(40, 800), fitz.Point(555, 800), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text(fitz.Point(40, 815), f"Department of Computer Science & Engineering • Padika AI Learning System", fontsize=8, color=(0.5, 0.5, 0.5))
        page.insert_text(fitz.Point(510, 815), f"Page {page_idx + 1}", fontsize=9, color=(0.3, 0.3, 0.3))

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc.save(filepath)
    doc.close()
    return filepath

def initialize_database():
    print("✦ [Padika AI] Initializing SQLite database schema...")
    base_dir = Path(__file__).resolve().parent
    schema_path = base_dir / 'app' / 'schema.sql'
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    with get_db() as conn:
        conn.executescript(schema_sql)

    print("✓ Schema initialized successfully.")

    # 1. Academic Years
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO academic_years (id, name, is_current) VALUES (1, '2025-2026', 1)")

    # 2. Semesters 1 through 8
    semesters_data = [
        (1, 'Semester 1', 1, 1),
        (2, 'Semester 2', 2, 1),
        (3, 'Semester 3', 3, 1),
        (4, 'Semester 4', 4, 1),
        (5, 'Semester 5', 5, 1),
        (6, 'Semester 6', 6, 1),
        (7, 'Semester 7', 7, 1),
        (8, 'Semester 8', 8, 1),
    ]
    with get_db() as conn:
        conn.executemany("INSERT OR IGNORE INTO semesters (id, name, number, academic_year_id) VALUES (?, ?, ?, ?)", semesters_data)

    # 3. Departments
    departments_data = [
        (1, 'Computer Science and Engineering', 'CSE', 'Core algorithms, software architectures, artificial intelligence, and network systems.'),
        (2, 'Artificial Intelligence & Data Science', 'AI&DS', 'Machine learning, deep neural representations, and big data systems.'),
        (3, 'Information Technology', 'IT', 'Cloud systems, enterprise web applications, and cyber-security architectures.'),
        (4, 'Electronics and Communication Engineering', 'ECE', 'Embedded systems, VLSI signal processing, and communication networks.')
    ]
    with get_db() as conn:
        conn.executemany("INSERT OR IGNORE INTO departments (id, name, code, description) VALUES (?, ?, ?, ?)", departments_data)

    # 4. Subjects
    subjects_data = [
        (1, 'CS3691', 'Artificial Intelligence and Machine Learning', 1, 6, 4, 'Covers Supervised Learning, Deep Neural Networks, CNN architectures, Natural Language Processing, and Reinforcement Learning.'),
        (2, 'CS3591', 'Computer Networks and Security', 1, 5, 4, 'Covers OSI & TCP/IP stack, Flow and Congestion Control, Routing Protocols (OSPF, BGP), and Cryptographic security.'),
        (3, 'CS3492', 'Database Management Systems', 1, 4, 3, 'Covers Relational Algebra, SQL Normalization (1NF to BCNF), ACID Transactions, B+ Tree Indexing, and Query Optimization.'),
        (4, 'CS3351', 'Digital Principles and Computer Organization', 1, 3, 4, 'Covers Boolean logic, ALU design, RISC pipelining, cache memory hierarchies, and virtual memory systems.')
    ]
    with get_db() as conn:
        conn.executemany("INSERT OR IGNORE INTO subjects (id, code, name, department_id, semester_id, credits, description) VALUES (?, ?, ?, ?, ?, ?, ?)", subjects_data)

    # 5. Core Users (Admin, Faculty, Student)
    print("✦ Seeding core users...")
    if not UserModel.get_by_email('admin@padika.ai'):
        UserModel.create(
            full_name='Padika Campus Administrator',
            email='admin@padika.ai',
            password='Admin@123',
            role='admin'
        )

    if not UserModel.get_by_email('faculty@padika.ai'):
        UserModel.create(
            full_name='Dr. K. Ramanathan, Ph.D.',
            email='faculty@padika.ai',
            password='Faculty@123',
            role='faculty',
            department_id=1,
            employee_id='FAC-CSE-001'
        )

    if not UserModel.get_by_email('student@padika.ai'):
        UserModel.create(
            full_name='Ananya Sundaram',
            email='student@padika.ai',
            password='Student@123',
            role='student',
            department_id=1,
            semester_id=6,
            roll_number='714022104015'
        )

    faculty_user = UserModel.get_by_email('faculty@padika.ai')
    student_user = UserModel.get_by_email('student@padika.ai')

    # 6. Generate and Seed Realistic Academic PDFs
    print("✦ Creating academic PDFs with genuine curriculum text and generating vector embeddings...")
    uploads_dir = Path(Config.UPLOAD_FOLDER)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    materials_seed_configs = [
        {
            'title': 'Unit 1: Foundations of Machine Learning & Neural Networks',
            'desc': 'Complete lecture notes on Supervised Learning algorithms, Cost Functions, Backpropagation, and Convolutional Neural Network (CNN) feature extraction.',
            'category': 'Notes',
            'subject_id': 1, # CS3691
            'dept_id': 1,
            'sem_id': 6,
            'filename': 'CS3691_Unit1_Machine_Learning.pdf',
            'pages': [
                (
                    "Introduction to Machine Learning Paradigms",
                    [
                        ("1.1 Definition and Core Concepts",
                         "Machine learning is a subfield of artificial intelligence that gives computers the ability to learn without being explicitly programmed. In a classic definition by Tom Mitchell (1997): A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P, if its performance at tasks in T, as measured by P, improves with experience E.\n\nKey learning paradigms include:\n1. Supervised Learning: Training data includes input features paired with ground-truth target labels. Examples: Linear Regression, Logistic Regression, Support Vector Machines, Random Forests.\n2. Unsupervised Learning: Algorithms discover hidden patterns, intrinsic clusters, or probability distributions without explicit labels. Examples: K-Means clustering, Principal Component Analysis (PCA), Autoencoders.\n3. Reinforcement Learning: An autonomous agent learns optimal policies through sequential trial-and-error feedback from an environment using rewards and penalties."),
                        ("1.2 Cost Functions and Gradient Descent Optimization",
                         "Supervised models minimize an objective cost function J(theta). For regression, the Mean Squared Error (MSE) is commonly used:\n   J(theta) = (1/2m) * sum((h_theta(x^(i)) - y^(i))^2)\n\nGradient Descent iteratively updates model parameters in the direction of steepest decrease:\n   theta_j := theta_j - alpha * (d/d theta_j) J(theta)\nwhere alpha is the learning rate. Critical variants include Batch Gradient Descent, Stochastic Gradient Descent (SGD), and Adam (Adaptive Moment Estimation) which computes individual adaptive learning rates for different parameters from estimates of first and second moments of the gradients.")
                    ]
                ),
                (
                    "Deep Neural Networks & Convolutional Architectures",
                    [
                        ("2.1 Multilayer Perceptron and Backpropagation",
                         "A Multilayer Perceptron (MLP) consists of an input layer, one or more hidden layers, and an output layer. Neurons compute an affine transformation followed by a non-linear activation function:\n   z = W * x + b\n   a = sigma(z)\nPopular activation functions include Sigmoid, Tanh, and Rectified Linear Unit (ReLU: f(x) = max(0, x)). ReLU mitigates the vanishing gradient problem in deep networks. Backpropagation calculates the partial derivative of the error function with respect to every weight using the mathematical chain rule, propagating error deltas backward through the network layers."),
                        ("2.2 Convolutional Neural Networks (CNN) Architecture",
                         "Convolutional Neural Networks are specialized architectures designed for processing spatial grid-structured data like images. A standard CNN comprises:\n1. Convolutional Layer: Learns spatial filter kernels (e.g. 3x3, 5x5) that slide across the input to produce feature maps, preserving spatial locality.\n2. Non-linear Activation: Applied elementwise (ReLU).\n3. Pooling Layer: Downsamples spatial dimensions (Max Pooling or Average Pooling), ensuring translation invariance and reducing parameter count.\n4. Fully Connected (FC) Layer: Flattened feature maps are classified into target class probabilities via Softmax activation.")
                    ]
                ),
                (
                    "Examination Review & 2-Mark / 16-Mark Summary",
                    [
                        ("3.1 Frequent 2-Mark Questions & Answers",
                         "Q1: Define Overfitting and state two methods to prevent it.\nAnswer: Overfitting occurs when a model learns the training noise rather than the general underlying relationship, leading to high training accuracy but poor generalization on test data. Prevention methods include L1/L2 Regularization (Weight Decay), Dropout (p=0.5), Early Stopping, and Data Augmentation.\n\nQ2: What is the Vanishing Gradient problem?\nAnswer: In deep networks with saturating activations like Sigmoid, gradients become exponentially small as backpropagation traverses backward, causing early layers to train extremely slowly. It is resolved using ReLU or residual connections."),
                        ("3.2 16-Mark Question Blueprint: CNN Architecture and Working",
                         "A full 16-mark answer on CNNs requires:\n1. Introduction: Need for spatial feature extraction over standard MLPs (parameter sharing and sparse interactions).\n2. Architectural Diagram: Input Image -> [Conv2D + ReLU + MaxPool] x N -> Flatten -> Dense -> Softmax Output.\n3. Detailed Mathematical formulation of 2D Convolution: S(i, j) = (I * K)(i, j) = sum_m sum_n I(i-m, j-n) K(m, n).\n4. Stride and Padding (Valid vs Same Padding).\n5. Applications: Object detection (YOLO), semantic segmentation, facial recognition, and medical imaging.")
                    ]
                )
            ]
        },
        {
            'title': 'Unit 2: Computer Networks & Protocol Architectures',
            'desc': 'In-depth notes on the OSI Reference Model, TCP 3-Way Handshake, Sliding Window flow control, and Congestion Control algorithms.',
            'category': 'Notes',
            'subject_id': 2, # CS3591
            'dept_id': 1,
            'sem_id': 5,
            'filename': 'CS3591_Unit2_Computer_Networks.pdf',
            'pages': [
                (
                    "The OSI 7-Layer Reference Model and TCP/IP Stack",
                    [
                        ("1.1 Layer-by-Layer Architectural Analysis",
                         "The Open Systems Interconnection (OSI) model organizes network communication into seven hierarchical layers:\n1. Physical Layer: Transmission of raw unstructured bit streams over physical medium (cables, fiber, radio).\n2. Data Link Layer: Node-to-node frame delivery, framing, error detection (CRC), and MAC addressing (Ethernet, Wi-Fi).\n3. Network Layer: Logical host-to-host addressing (IPv4, IPv6) and routing packet delivery across multiple networks (Routers).\n4. Transport Layer: End-to-end process-to-process communication, segmentation, flow control, and port addressing (TCP, UDP).\n5. Session Layer: Establishes, manages, and terminates presentation sessions.\n6. Presentation Layer: Translation, encryption (TLS/SSL), and data compression.\n7. Application Layer: Direct network interface for end-user applications (HTTP, DNS, SMTP, FTP)."),
                        ("1.2 Comparison: TCP vs UDP Protocols",
                         "Transmission Control Protocol (TCP):\n- Connection-oriented protocol requiring 3-way handshake before data transfer.\n- Guarantees ordered, reliable delivery with ACK acknowledgement and retransmissions.\n- Includes congestion control and flow control.\n- Header size: 20 to 60 bytes.\n\nUser Datagram Protocol (UDP):\n- Connectionless, lightweight transport protocol with no handshake.\n- Unreliable best-effort delivery: packets may arrive out-of-order or get lost.\n- Low latency, ideal for real-time applications like VoIP, DNS, and video streaming.\n- Minimal header size: 8 bytes.")
                    ]
                ),
                (
                    "Transport Layer Mechanisms: Handshake & Congestion Control",
                    [
                        ("2.1 TCP 3-Way Handshake Connection Establishment",
                         "To establish a reliable full-duplex TCP connection:\n1. SYN: Client sends a TCP segment with SYN=1 and a random initial sequence number (ISN_client = x).\n2. SYN-ACK: Server receives SYN, allocates buffers/variables, and responds with SYN=1, ACK=1, ack_number = x + 1, and its own initial sequence number (ISN_server = y).\n3. ACK: Client sends ACK=1, ack_number = y + 1. The connection is established, and data transfer can commence.\n\nConnection termination uses a 4-step FIN-ACK handshake: FIN -> ACK -> FIN -> ACK."),
                        ("2.2 TCP Congestion Control Algorithms",
                         "TCP regulates transmission rate using a dynamic Congestion Window (cwnd):\n1. Slow Start: cwnd starts at 1 MSS and doubles every RTT (exponential growth: 1, 2, 4, 8, ...) until reaching slow start threshold (ssthresh).\n2. Congestion Avoidance: Once cwnd >= ssthresh, cwnd increases linearly by 1 MSS per RTT (additive increase).\n3. Congestion Detection: If a timeout occurs, ssthresh is set to cwnd / 2, and cwnd resets to 1 MSS. If 3 duplicate ACKs are received, Fast Retransmit and Fast Recovery halve cwnd without resetting to 1 MSS.")
                    ]
                )
            ]
        },
        {
            'title': 'Unit 3: Database Management Systems — Normalization & Transactions',
            'desc': 'Lecture notes on Functional Dependencies, 1NF, 2NF, 3NF, BCNF Normalization forms, and ACID properties with transaction scheduling.',
            'category': 'Notes',
            'subject_id': 3, # CS3492
            'dept_id': 1,
            'sem_id': 4,
            'filename': 'CS3492_Unit3_Database_Management_Systems.pdf',
            'pages': [
                (
                    "Relational Database Normalization (1NF to BCNF)",
                    [
                        ("1.1 Purpose of Normalization and Anomalies",
                         "Database normalization is the systematic process of organizing relation schemas to minimize data redundancy and eliminate undesirable update, insertion, and deletion anomalies.\n- Insertion Anomaly: Inability to insert certain facts without introducing unrelated null attributes.\n- Deletion Anomaly: Deleting one piece of information inadvertently destroys unrelated critical facts.\n- Update Anomaly: Inconsistent updates across multiple duplicated records."),
                        ("1.2 Normal Forms Breakdown",
                         "1NF (First Normal Form): Every attribute must hold atomic (indivisible) values; repeating groups or multi-valued columns are forbidden.\n\n2NF (Second Normal Form): Relation must be in 1NF and have NO partial functional dependencies. Every non-prime attribute must depend entirely on the whole candidate key, not a proper subset of it.\n\n3NF (Third Normal Form): Relation must be in 2NF and have NO transitive functional dependencies. For every non-trivial functional dependency X -> Y, either X is a superkey, or Y is a prime attribute.\n\nBCNF (Boyce-Codd Normal Form): A stricter version of 3NF where for EVERY functional dependency X -> Y, X MUST be a superkey.")
                    ]
                ),
                (
                    "Transaction Management & ACID Properties",
                    [
                        ("2.1 ACID Properties of Database Transactions",
                         "A transaction is a logical unit of work that accesses and potentially modifies database items. It must strictly satisfy the ACID criteria:\n1. Atomicity: All operations in a transaction execute completely, or none do (All-or-Nothing). Managed by the Recovery Manager.\n2. Consistency: Execution of a transaction in isolation preserves database integrity constraints.\n3. Isolation: Concurrent execution of transactions yields the same database state as if they were executed serially. Managed by the Concurrency Control manager (Locks, Timestamps).\n4. Durability: Once a transaction commits, its modifications persist permanently, even during power failures or system crashes. Managed by Write-Ahead Logging (WAL)."),
                        ("2.2 B+ Tree Indexing Architecture",
                         "B+ Trees are balanced n-ary search trees widely utilized in relational databases for efficient disk block indexing:\n- All actual records/pointers reside exclusively in the leaf nodes.\n- Leaf nodes are linked together as a doubly-linked list, enabling fast sequential range queries O(log N + K).\n- Internal nodes store only search keys and child page pointers.\n- Guaranteed logarithmic time complexity O(log N) for search, insertion, and deletion operations.")
                    ]
                )
            ]
        }
    ]

    for m_cfg in materials_seed_configs:
        pdf_file_path = str(uploads_dir / m_cfg['filename'])
        create_sample_pdf(pdf_file_path, m_cfg['title'], f"Subject {m_cfg['subject_id']}", m_cfg['pages'])
        file_size = os.path.getsize(pdf_file_path)

        # Create or update Material record
        existing = MaterialModel.get_filtered(search=m_cfg['title'])
        if existing:
            mat_id = existing[0]['id']
            ChunkModel.delete_by_material(mat_id)
        else:
            mat_id = MaterialModel.create(
                title=m_cfg['title'],
                description=m_cfg['desc'],
                category=m_cfg['category'],
                filename=m_cfg['filename'],
                original_filename=m_cfg['filename'],
                file_size=file_size,
                mime_type='application/pdf',
                file_path=pdf_file_path,
                subject_id=m_cfg['subject_id'],
                department_id=m_cfg['dept_id'],
                semester_id=m_cfg['sem_id'],
                faculty_id=faculty_user['id']
            )

        # Extract pages, chunk, and embed
        pages = PDFService.extract_text_with_pages(pdf_file_path)
        chunks = PDFService.chunk_document(pages)
        contents = [c['content'] for c in chunks]
        embeddings = EmbeddingService.generate_embeddings_batch(contents)

        chunk_tuples = []
        for c, emb in zip(chunks, embeddings):
            chunk_tuples.append((
                mat_id,
                c['page_number'],
                c['chunk_index'],
                c['content'],
                json.dumps(emb)
            ))

        ChunkModel.insert_bulk(chunk_tuples)
        MaterialModel.update_status(mat_id, 'Completed', page_count=len(pages), chunk_count=len(chunks))
        print(f"  ✓ Indexed: {m_cfg['title']} ({len(pages)} pages, {len(chunks)} chunks)")

    # 7. Seed sample initial bookmark for student
    sample_mat = MaterialModel.get_filtered()[0]
    BookmarkModel.toggle(student_user['id'], sample_mat['id'], notes="Important for upcoming internal exam!")

    # 8. Seed sample chat conversation
    sess_id = ChatModel.create_session(
        user_id=student_user['id'],
        title="Supervised Learning vs Unsupervised",
        subject_id=1,
        material_id=sample_mat['id'],
        language='en',
        format_pref='13-mark'
    )
    ChatModel.add_message(sess_id, 'user', 'What is Supervised Learning and how does it compare to Unsupervised Learning?')
    ChatModel.add_message(
        sess_id,
        'ai',
        """### Supervised vs Unsupervised Learning — 13-Mark Comprehensive Answer

## 1. Introduction & Definitions
According to your faculty course notes in **Unit 1: Foundations of Machine Learning & Neural Networks** (Page 1):
- **Supervised Learning:** Algorithms train on labeled data where inputs are explicitly paired with corresponding ground-truth targets. The goal is learning a mapping function `y = f(x)`.
- **Unsupervised Learning:** Algorithms operate on unlabeled input vectors to uncover hidden structures, groupings, or distributions without target feedback.

## 2. Core Architectural & Operational Differences
| Parameter | Supervised Learning | Unsupervised Learning |
| :--- | :--- | :--- |
| **Input Data** | Labeled dataset `(x_i, y_i)` | Unlabeled data `(x_i)` only |
| **Objective** | Predict outputs for unseen inputs | Discover natural clusters or latent factors |
| **Feedback** | Direct error feedback via ground truth | No direct feedback (heuristic optimization) |
| **Key Algorithms**| Linear/Logistic Regression, SVM, CNN | K-Means, PCA, Autoencoders |

## 3. Working Mechanism & Cost Optimization
From **Unit 1: Foundations of Machine Learning & Neural Networks** (Page 1):
Supervised algorithms minimize an objective cost function such as Mean Squared Error (MSE) using Gradient Descent:
`theta_j := theta_j - alpha * (d/d theta_j) J(theta)`

In contrast, unsupervised algorithms like K-Means minimize inertia (within-cluster sum-of-squares).

## 4. Exam Conclusion & Citations
- **Document Reference:** Unit 1: Foundations of Machine Learning & Neural Networks.pdf
- **Page Citation:** Page 1""",
        sources=[{
            'material_id': sample_mat['id'],
            'document_title': sample_mat['title'],
            'page_number': 1,
            'subject_name': 'Artificial Intelligence and Machine Learning',
            'score': 0.94,
            'snippet': 'Supervised Learning: Training data includes input features paired with ground-truth target labels...'
        }]
    )

    print("✦ [Padika AI] Initialization and demo data generation complete!")

if __name__ == '__main__':
    initialize_database()
