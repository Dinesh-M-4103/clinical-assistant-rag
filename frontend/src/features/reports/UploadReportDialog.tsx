import { zodResolver } from '@hookform/resolvers/zod';
import { Controller, useForm } from 'react-hook-form';
import { useUploadReport } from '@/api/hooks/reports';
import { CATEGORIES } from '@/api/schemas';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { Spinner } from '@/components/ui/spinner';
import { CATEGORY_LABELS } from '@/lib/categories';
import { describeError } from '@/lib/errors';
import { MAX_UPLOAD_MB } from '@/lib/env';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { FileDropzone } from './FileDropzone';
import { nameFromFilename, reportUploadSchema, type ReportUploadValues } from './uploadSchema';

function ProcessingNotice() {
  return (
    <div
      role="status"
      className="space-y-2 rounded-lg bg-primary-soft px-4 py-3 text-sm text-primary-text"
    >
      <div className="flex items-center gap-2 font-medium">
        <Spinner /> Uploading and indexing…
      </div>
      <p className="text-xs">
        Extracting text, splitting it into passages and building the search index.
      </p>
      <div className="h-1.5 overflow-hidden rounded-full bg-primary/20">
        <div className="h-full w-1/3 animate-indeterminate rounded-full bg-primary" />
      </div>
    </div>
  );
}

function UploadForm({ uhid, onDone }: { uhid: string; onDone: () => void }) {
  const upload = useUploadReport(uhid);
  const {
    control,
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<ReportUploadValues>({
    resolver: zodResolver(reportUploadSchema),
    defaultValues: { name: '', category: 'lab', notes: '' },
  });

  const submit = handleSubmit((values) =>
    upload.mutate({ ...values, notes: values.notes || undefined }, { onSuccess: onDone }),
  );

  return (
    <form onSubmit={submit} noValidate className="flex min-h-0 flex-1 flex-col">
      <DialogBody className="space-y-4">
        <Field label="PDF file" error={errors.file?.message} hint={`Up to ${MAX_UPLOAD_MB} MB`}>
          {({ id, describedBy, invalid }) => (
            <Controller
              control={control}
              name="file"
              render={({ field }) => (
                <FileDropzone
                  id={id}
                  file={field.value}
                  describedBy={describedBy}
                  invalid={invalid}
                  disabled={upload.isPending}
                  onFile={(file) => {
                    field.onChange(file);
                    if (!getValues('name')) {
                      setValue('name', nameFromFilename(file.name), { shouldValidate: true });
                    }
                  }}
                />
              )}
            />
          )}
        </Field>
        <Field label="Report name" error={errors.name?.message}>
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              disabled={upload.isPending}
              aria-describedby={describedBy}
              aria-invalid={invalid}
              {...register('name')}
            />
          )}
        </Field>
        <Field label="Category">
          {({ id }) => (
            <Select id={id} disabled={upload.isPending} {...register('category')}>
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {CATEGORY_LABELS[category]}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Notes (optional)" error={errors.notes?.message}>
          {({ id, describedBy, invalid }) => (
            <Textarea
              id={id}
              rows={2}
              disabled={upload.isPending}
              aria-describedby={describedBy}
              aria-invalid={invalid}
              {...register('notes')}
            />
          )}
        </Field>
        {upload.isPending && <ProcessingNotice />}
        {upload.isError && (
          <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">
            {describeError(upload.error)}
          </p>
        )}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone} disabled={upload.isPending}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={upload.isPending}>
          {upload.isPending ? <Spinner /> : null}
          Upload report
        </Button>
      </DialogFooter>
    </form>
  );
}

export function UploadReportDialog({ uhid }: { uhid: string }) {
  const open = useWorkspace((state) => state.uploadOpen);
  const setOpen = useWorkspace((state) => state.setUploadOpen);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent onInteractOutside={(event) => event.preventDefault()}>
        <DialogHeader>
          <DialogTitle>Upload report</DialogTitle>
          <DialogDescription>
            Add a PDF to this patient&rsquo;s records so it can be searched and cited.
          </DialogDescription>
        </DialogHeader>
        <UploadForm uhid={uhid} onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
