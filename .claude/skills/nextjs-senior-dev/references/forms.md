# Forms

## React Hook Form + Zod

### Installation

```bash
npm install react-hook-form @hookform/resolvers zod
```

### Basic Form Setup

```typescript
// features/contact/components/ContactForm.interactive.tsx
"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { submitContact } from "../actions/submit-contact"

const contactSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  message: z.string().min(10, "Message must be at least 10 characters"),
})

type ContactFormData = z.infer<typeof contactSchema>

export function ContactForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      name: "",
      email: "",
      message: "",
    },
  })

  const onSubmit = async (data: ContactFormData) => {
    const result = await submitContact(data)

    if (result.success) {
      reset()
      // Show success toast
    } else {
      // Show error toast
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="name">Name</label>
        <input
          id="name"
          {...register("name")}
          className={errors.name ? "border-red-500" : ""}
        />
        {errors.name && (
          <p className="text-red-500 text-sm">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          {...register("email")}
          className={errors.email ? "border-red-500" : ""}
        />
        {errors.email && (
          <p className="text-red-500 text-sm">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="message">Message</label>
        <textarea
          id="message"
          {...register("message")}
          rows={4}
          className={errors.message ? "border-red-500" : ""}
        />
        {errors.message && (
          <p className="text-red-500 text-sm">{errors.message.message}</p>
        )}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Sending..." : "Send Message"}
      </button>
    </form>
  )
}
```

### Server Action

```typescript
// features/contact/actions/submit-contact.ts
"use server"

import { z } from "zod"

const contactSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  message: z.string().min(10),
})

export async function submitContact(data: z.infer<typeof contactSchema>) {
  // Validate again on server (never trust client)
  const validated = contactSchema.safeParse(data)

  if (!validated.success) {
    return {
      success: false,
      error: "Invalid form data",
      fieldErrors: validated.error.flatten().fieldErrors,
    }
  }

  try {
    // Send email, save to DB, etc.
    await sendEmail(validated.data)

    return { success: true }
  } catch (error) {
    console.error("Contact form error:", error)
    return { success: false, error: "Failed to send message" }
  }
}
```

## Native Server Actions with useActionState

### Form Component

```typescript
// features/posts/components/CreatePostForm.interactive.tsx
"use client"

import { useActionState } from "react"
import { useFormStatus } from "react-dom"
import { createPost } from "../actions/create-post"

const initialState = {
  success: false,
  error: null as string | null,
  fieldErrors: {} as Record<string, string[]>,
}

export function CreatePostForm() {
  const [state, formAction] = useActionState(createPost, initialState)

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <div className="bg-red-50 text-red-500 p-3 rounded">
          {state.error}
        </div>
      )}

      {state.success && (
        <div className="bg-green-50 text-green-500 p-3 rounded">
          Post created successfully!
        </div>
      )}

      <div>
        <label htmlFor="title">Title</label>
        <input
          id="title"
          name="title"
          required
          className={state.fieldErrors?.title ? "border-red-500" : ""}
        />
        {state.fieldErrors?.title && (
          <p className="text-red-500 text-sm">{state.fieldErrors.title[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          name="content"
          rows={6}
          required
          className={state.fieldErrors?.content ? "border-red-500" : ""}
        />
        {state.fieldErrors?.content && (
          <p className="text-red-500 text-sm">{state.fieldErrors.content[0]}</p>
        )}
      </div>

      <SubmitButton />
    </form>
  )
}

function SubmitButton() {
  const { pending } = useFormStatus()

  return (
    <button type="submit" disabled={pending}>
      {pending ? "Creating..." : "Create Post"}
    </button>
  )
}
```

### Server Action with FormData

```typescript
// features/posts/actions/create-post.ts
"use server"

import { auth } from "@/auth"
import { z } from "zod"
import { revalidateTag } from "next/cache"
import { db } from "@/lib/db/client"

const createPostSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  content: z.string().min(1, "Content is required"),
})

type ActionState = {
  success: boolean
  error: string | null
  fieldErrors: Record<string, string[]>
}

export async function createPost(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  // 1. Auth
  const session = await auth()
  if (!session?.user) {
    return { success: false, error: "Unauthorized", fieldErrors: {} }
  }

  // 2. Validate
  const validated = createPostSchema.safeParse({
    title: formData.get("title"),
    content: formData.get("content"),
  })

  if (!validated.success) {
    return {
      success: false,
      error: "Please fix the errors below",
      fieldErrors: validated.error.flatten().fieldErrors,
    }
  }

  // 3. Create
  try {
    await db.post.create({
      data: {
        ...validated.data,
        authorId: session.user.id,
      },
    })

    revalidateTag("posts")

    return { success: true, error: null, fieldErrors: {} }
  } catch (error) {
    return { success: false, error: "Failed to create post", fieldErrors: {} }
  }
}
```

## Multi-Step Forms

### Form Context

```typescript
// features/onboarding/context/FormContext.tsx
"use client"

import { createContext, useContext, useState, ReactNode } from "react"

interface FormData {
  // Step 1
  name: string
  email: string
  // Step 2
  company: string
  role: string
  // Step 3
  plan: string
  billing: string
}

interface FormContextType {
  data: Partial<FormData>
  updateData: (step: Partial<FormData>) => void
  currentStep: number
  setCurrentStep: (step: number) => void
  totalSteps: number
}

const FormContext = createContext<FormContextType | null>(null)

export function FormProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<Partial<FormData>>({})
  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 3

  const updateData = (step: Partial<FormData>) => {
    setData((prev) => ({ ...prev, ...step }))
  }

  return (
    <FormContext.Provider
      value={{ data, updateData, currentStep, setCurrentStep, totalSteps }}
    >
      {children}
    </FormContext.Provider>
  )
}

export function useFormContext() {
  const context = useContext(FormContext)
  if (!context) {
    throw new Error("useFormContext must be used within FormProvider")
  }
  return context
}
```

### Step Components

```typescript
// features/onboarding/components/Step1.interactive.tsx
"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useFormContext } from "../context/FormContext"

const step1Schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
})

export function Step1() {
  const { data, updateData, setCurrentStep } = useFormContext()

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(step1Schema),
    defaultValues: {
      name: data.name || "",
      email: data.email || "",
    },
  })

  const onSubmit = (formData: z.infer<typeof step1Schema>) => {
    updateData(formData)
    setCurrentStep(2)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <h2>Personal Information</h2>

      <input {...register("name")} placeholder="Name" />
      {errors.name && <span>{errors.name.message}</span>}

      <input {...register("email")} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}

      <button type="submit">Next</button>
    </form>
  )
}
```

### Multi-Step Form Container

```typescript
// features/onboarding/components/OnboardingForm.interactive.tsx
"use client"

import { FormProvider, useFormContext } from "../context/FormContext"
import { Step1 } from "./Step1.interactive"
import { Step2 } from "./Step2.interactive"
import { Step3 } from "./Step3.interactive"

function FormSteps() {
  const { currentStep, totalSteps } = useFormContext()

  return (
    <div>
      {/* Progress indicator */}
      <div className="flex mb-8">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div
            key={i}
            className={`flex-1 h-2 ${
              i + 1 <= currentStep ? "bg-blue-500" : "bg-gray-200"
            }`}
          />
        ))}
      </div>

      {/* Current step */}
      {currentStep === 1 && <Step1 />}
      {currentStep === 2 && <Step2 />}
      {currentStep === 3 && <Step3 />}
    </div>
  )
}

export function OnboardingForm() {
  return (
    <FormProvider>
      <FormSteps />
    </FormProvider>
  )
}
```

## File Uploads

### Upload Component

```typescript
// components/shared/FileUpload.interactive.tsx
"use client"

import { useState, useRef } from "react"

interface FileUploadProps {
  onUpload: (url: string) => void
  accept?: string
  maxSize?: number // in MB
}

export function FileUpload({
  onUpload,
  accept = "image/*",
  maxSize = 5,
}: FileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate size
    if (file.size > maxSize * 1024 * 1024) {
      setError(`File must be less than ${maxSize}MB`)
      return
    }

    // Preview for images
    if (file.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(file))
    }

    setError(null)
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("Upload failed")

      const { url } = await response.json()
      onUpload(url)
    } catch (err) {
      setError("Failed to upload file")
      setPreview(null)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
      >
        {uploading ? "Uploading..." : "Choose File"}
      </button>

      {error && <p className="text-red-500">{error}</p>}

      {preview && (
        <img src={preview} alt="Preview" className="mt-2 max-w-xs" />
      )}
    </div>
  )
}
```

### Upload API Route

```typescript
// app/api/upload/route.ts
import { NextRequest, NextResponse } from "next/server"
import { auth } from "@/auth"
import { put } from "@vercel/blob"

export async function POST(request: NextRequest) {
  const session = await auth()
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const formData = await request.formData()
  const file = formData.get("file") as File

  if (!file) {
    return NextResponse.json({ error: "No file provided" }, { status: 400 })
  }

  // Validate file type
  const allowedTypes = ["image/jpeg", "image/png", "image/webp"]
  if (!allowedTypes.includes(file.type)) {
    return NextResponse.json({ error: "Invalid file type" }, { status: 400 })
  }

  // Upload to Vercel Blob
  const blob = await put(`uploads/${Date.now()}-${file.name}`, file, {
    access: "public",
  })

  return NextResponse.json({ url: blob.url })
}
```

## Dynamic Form Fields

```typescript
// features/survey/components/DynamicForm.interactive.tsx
"use client"

import { useFieldArray, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

const questionSchema = z.object({
  text: z.string().min(1, "Question text is required"),
  type: z.enum(["text", "select", "checkbox"]),
  options: z.array(z.string()).optional(),
})

const surveySchema = z.object({
  title: z.string().min(1),
  questions: z.array(questionSchema).min(1, "Add at least one question"),
})

type SurveyFormData = z.infer<typeof surveySchema>

export function DynamicSurveyForm() {
  const { control, register, handleSubmit, formState: { errors } } = useForm<SurveyFormData>({
    resolver: zodResolver(surveySchema),
    defaultValues: {
      title: "",
      questions: [{ text: "", type: "text", options: [] }],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "questions",
  })

  const onSubmit = (data: SurveyFormData) => {
    console.log(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label>Survey Title</label>
        <input {...register("title")} />
        {errors.title && <span>{errors.title.message}</span>}
      </div>

      <div className="space-y-4">
        <h3>Questions</h3>

        {fields.map((field, index) => (
          <div key={field.id} className="border p-4 rounded">
            <div className="flex justify-between">
              <span>Question {index + 1}</span>
              {fields.length > 1 && (
                <button type="button" onClick={() => remove(index)}>
                  Remove
                </button>
              )}
            </div>

            <input
              {...register(`questions.${index}.text`)}
              placeholder="Question text"
            />

            <select {...register(`questions.${index}.type`)}>
              <option value="text">Text</option>
              <option value="select">Select</option>
              <option value="checkbox">Checkbox</option>
            </select>
          </div>
        ))}

        <button
          type="button"
          onClick={() => append({ text: "", type: "text", options: [] })}
        >
          Add Question
        </button>
      </div>

      <button type="submit">Create Survey</button>
    </form>
  )
}
```

## Form Validation Patterns

### Shared Schemas

```typescript
// lib/validations/user.ts
import { z } from "zod"

export const emailSchema = z.string().email("Invalid email address")

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Must contain uppercase letter")
  .regex(/[a-z]/, "Must contain lowercase letter")
  .regex(/[0-9]/, "Must contain number")
  .regex(/[^A-Za-z0-9]/, "Must contain special character")

export const userSchema = z.object({
  name: z.string().min(2).max(100),
  email: emailSchema,
  password: passwordSchema,
})

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
})

export const updateProfileSchema = userSchema.omit({ password: true }).partial()
```

### Async Validation

```typescript
// Check if email exists during registration
const registerSchema = z.object({
  email: z
    .string()
    .email()
    .refine(
      async (email) => {
        const exists = await checkEmailExists(email)
        return !exists
      },
      { message: "Email already registered" }
    ),
  password: passwordSchema,
})

// In the form
const { register, handleSubmit, formState: { errors, isValidating } } = useForm({
  resolver: zodResolver(registerSchema),
  mode: "onBlur", // Validate on blur for async
})
```

## Optimistic Updates

```typescript
// features/todos/components/TodoList.interactive.tsx
"use client"

import { useOptimistic, useTransition } from "react"
import { toggleTodo } from "../actions/toggle-todo"

interface Todo {
  id: string
  text: string
  completed: boolean
}

export function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state, updatedId: string) =>
      state.map((todo) =>
        todo.id === updatedId ? { ...todo, completed: !todo.completed } : todo
      )
  )

  const [isPending, startTransition] = useTransition()

  const handleToggle = (id: string) => {
    startTransition(async () => {
      addOptimisticTodo(id)
      await toggleTodo(id)
    })
  }

  return (
    <ul>
      {optimisticTodos.map((todo) => (
        <li key={todo.id}>
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() => handleToggle(todo.id)}
            disabled={isPending}
          />
          <span className={todo.completed ? "line-through" : ""}>
            {todo.text}
          </span>
        </li>
      ))}
    </ul>
  )
}
```

## Form Best Practices

| Do | Don't |
|----|-------|
| Validate on server (never trust client) | Trust client-only validation |
| Show inline errors | Show all errors at top |
| Preserve form state on error | Reset form on error |
| Use optimistic updates | Wait for server response |
| Debounce async validation | Validate on every keystroke |
| Show loading states | Leave button enabled while submitting |
| Clear sensitive fields on submit | Keep passwords in state |
| Use `aria-invalid` for accessibility | Rely on color alone for errors |

## Forms Checklist

- [ ] Client + Server validation (same schema)
- [ ] Clear error messages per field
- [ ] Loading/pending states
- [ ] Success feedback
- [ ] Accessible labels and error announcements
- [ ] CSRF protection (automatic with Server Actions)
- [ ] Rate limiting on submission
- [ ] File upload size/type validation
- [ ] Optimistic updates where appropriate
- [ ] Form state preserved on validation errors